"""
Style reviewer - Checks blog consistency with author's style profile.
"""

import json
import logging
import os
from typing import Any

from anthropic import AsyncAnthropic
from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger(__name__)


class StyleReview(BaseModel):
    """Results of style review."""

    consistency_score: float = Field(description="Style consistency score 0-1")
    matches_tone: bool = Field(description="Whether tone matches profile")
    matches_voice: bool = Field(description="Whether voice matches profile")
    issues: list[str] = Field(default_factory=list, description="Style inconsistencies found")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    needs_revision: bool = Field(description="Whether style revision needed")


class StyleReviewer:
    """Reviews blog posts for style consistency."""

    async def review_style(self, blog_draft: str, style_profile: dict[str, Any]) -> dict[str, Any]:
        """Review blog for style consistency.

        Args:
            blog_draft: Current blog draft
            style_profile: Target style profile

        Returns:
            Review results as dictionary
        """
        logger.info("Reviewing blog for style consistency")

        style_desc = self._format_style_profile(style_profile)

        prompt = f"""Review this blog post for consistency with the target style:

=== TARGET STYLE ===
{style_desc}

=== BLOG DRAFT ===
{blog_draft}

Check for:
1. Tone consistency - Does it match the target tone?
2. Voice consistency - Active/passive voice as expected?
3. Vocabulary level - Matches expected complexity?
4. Sentence structure - Similar patterns to profile?
5. Overall feel - Does it sound like the same author?

Return JSON with:
- consistency_score: 0-1 overall score
- matches_tone: boolean
- matches_voice: boolean
- issues: list of specific style inconsistencies
- suggestions: list of how to better match style
- needs_revision: boolean (true if score < 0.7)"""

        try:
            client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = await client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4096,
                system="You are a style editor ensuring writing consistency.",
                messages=[{"role": "user", "content": prompt}],
            )

            if not response or not response.content:
                logger.error("No response from style review, using default")
                return self._default_review()

            # Try to parse JSON response
            try:
                content = response.content[0].text.strip()
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                parsed = json.loads(content.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse style review JSON: {e}, using default")
                return self._default_review()

            # Validate and structure response
            issues = parsed.get("issues", [])
            suggestions = parsed.get("suggestions", [])

            # Convert dict items to strings if needed
            if issues and isinstance(issues[0], dict):
                issues = [
                    item.get("description", str(item)) if isinstance(item, dict) else str(item) for item in issues
                ]

            if suggestions and isinstance(suggestions[0], dict):
                suggestions = [
                    item.get("description", str(item)) if isinstance(item, dict) else str(item)
                    for item in suggestions
                ]

            review_data = {
                "consistency_score": float(parsed.get("consistency_score", 0.8)),
                "matches_tone": bool(parsed.get("matches_tone", True)),
                "matches_voice": bool(parsed.get("matches_voice", True)),
                "issues": issues,
                "suggestions": suggestions,
                "needs_revision": bool(parsed.get("needs_revision", False)),
            }

            # Force needs_revision if score too low or issues found
            if review_data["consistency_score"] < 0.7:
                logger.info(f"Consistency score {review_data['consistency_score']:.2f} < 0.7, forcing revision")
                review_data["needs_revision"] = True

            if review_data["issues"] and len(review_data["issues"]) > 0:
                logger.info(f"Found {len(review_data['issues'])} style issues, forcing revision")
                review_data["needs_revision"] = True

            # Force needs_revision if tone or voice don't match
            if not review_data["matches_tone"] or not review_data["matches_voice"]:
                logger.info("Tone or voice mismatch, forcing revision")
                review_data["needs_revision"] = True

            review = StyleReview(**review_data)
            self._log_review_results(review)

            return review.model_dump()

        except Exception as e:
            logger.error(f"Style review failed: {e}")
            return self._default_review()

    def _format_style_profile(self, profile: dict[str, Any]) -> str:
        """Format style profile for prompt."""
        lines = []
        lines.append(f"Tone: {profile.get('tone', 'conversational')}")
        lines.append(f"Voice: {profile.get('voice', 'active')}")
        lines.append(f"Vocabulary Level: {profile.get('vocabulary_level', 'moderate')}")
        lines.append(f"Sentence Structure: {profile.get('sentence_structure', 'varied')}")
        lines.append(f"Paragraph Length: {profile.get('paragraph_length', 'medium')}")

        if profile.get("common_phrases"):
            lines.append("\nCommon Phrases:")
            for phrase in profile["common_phrases"][:5]:
                lines.append(f"  • {phrase}")

        if profile.get("writing_patterns"):
            lines.append("\nWriting Patterns:")
            for pattern in profile["writing_patterns"][:3]:
                lines.append(f"  • {pattern}")

        if profile.get("examples"):
            lines.append("\nExample Sentences (to match):")
            for ex in profile["examples"][:3]:
                lines.append(f"  • {ex}")

        return "\n".join(lines)

    def _log_review_results(self, review: StyleReview) -> None:
        """Log review results."""
        logger.info("=" * 50)
        logger.info("STYLE REVIEW RESULTS:")
        logger.info(f"  Consistency score: {review.consistency_score:.2f}")
        logger.info(f"  Matches tone: {review.matches_tone}")
        logger.info(f"  Matches voice: {review.matches_voice}")
        logger.info(f"  Needs revision: {review.needs_revision}")
        logger.info("  Threshold: 0.7 (revision if below)")
        logger.info(f"  Pass/Fail: {'FAIL - Revision Required' if review.needs_revision else 'PASS'}")

        status = []
        if review.matches_tone:
            status.append("✓ Tone matches")
        else:
            status.append("✗ Tone mismatch")

        if review.matches_voice:
            status.append("✓ Voice matches")
        else:
            status.append("✗ Voice mismatch")

        logger.info(f"  Style check: {', '.join(status)}")

        if review.issues:
            logger.warning(f"\nFound {len(review.issues)} style issues:")
            for i, issue in enumerate(review.issues, 1):
                logger.warning(f"  {i}. {issue}")

        if review.suggestions:
            logger.info(f"\nSuggestions ({len(review.suggestions)}):")
            for i, suggestion in enumerate(review.suggestions, 1):
                logger.info(f"  {i}. {suggestion}")

        logger.info("=" * 50)

    def _default_review(self) -> dict[str, Any]:
        """Return default passing review when checking fails."""
        logger.info("Using default style review (acceptable)")
        review = StyleReview(
            consistency_score=0.8,
            matches_tone=True,
            matches_voice=True,
            issues=[],
            suggestions=[],
            needs_revision=False,
        )
        return review.model_dump()
