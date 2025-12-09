"""
Video Analysis Service - Holistic Clinical Assessment

Analyzes uploaded child behavior videos using comprehensive
clinical + holistic developmental psychology framework.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import time

from app.models.artifact import Artifact
from app.prompts.video_analysis_prompt import build_video_analysis_prompt
from app.prompts.video_analysis_schema import get_video_analysis_schema
from app.services.llm.factory import create_llm_provider

logger = logging.getLogger(__name__)


class VideoAnalysisService:
    """
    Service for analyzing child behavior videos with holistic clinical framework.

    Combines:
    - Clinical observation standards (DSM-5, ICD-11)
    - Holistic developmental psychology (DIR/Floortime, strengths-based)
    - Parent persona awareness (vocabulary mirroring, emotional context)
    """

    def __init__(self, llm_provider=None):
        """
        Initialize video analysis service.

        Args:
            llm_provider: LLM provider with video/multimodal capabilities (optional)
        """
        if llm_provider is None:
            # Create strong LLM for video analysis
            import os
            # Use gemini-3-pro-preview - most current and capable model
            strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-3-pro-preview")
            provider_type = os.getenv("LLM_PROVIDER", "gemini")

            logger.info(f"🎥 Creating video-capable LLM for analysis: {strong_model}")
            self.llm_provider = create_llm_provider(
                provider_type=provider_type,
                model=strong_model,
                use_enhanced=False
            )
        else:
            self.llm_provider = llm_provider

        logger.info(f"VideoAnalysisService initialized with model: {getattr(self.llm_provider, 'model_name', 'unknown')}")

    async def analyze_video(
        self,
        video_path: str,
        child_data: Dict[str, Any],
        extracted_data: Dict[str, Any],
        analyst_context: Dict[str, Any],
        video_id: Optional[str] = None
    ) -> Artifact:
        """
        Perform comprehensive holistic clinical analysis on a video.

        Args:
            video_path: Path to video file
            child_data: Child demographics {name, age_years, age_months, gender}
            extracted_data: Full Stage 1 interview extraction
            analyst_context: Guideline-specific context from video_guidelines
            video_id: Optional video identifier

        Returns:
            Artifact with analysis results (status 'ready' or 'error')
        """
        artifact_id = f"video_analysis_{video_id}" if video_id else "video_analysis"
        start_time = time.time()

        child_name = child_data.get('name', 'Unknown')
        clinical_goal = analyst_context.get('clinical_goal', 'unknown')
        guideline_title = analyst_context.get('guideline_title', 'Unknown')

        logger.info(f"🎥 Starting video analysis for {child_name}")
        logger.info(f"   Clinical Goal: {clinical_goal}")
        logger.info(f"   Guideline: {guideline_title}")
        logger.info(f"   Video: {video_path}")

        # Create artifact in 'generating' state
        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type="analysis",
            status="generating",
            content_format="json",
            generation_inputs={
                "child_name": child_name,
                "clinical_goal": clinical_goal,
                "guideline_title": guideline_title,
                "video_path": video_path
            }
        )

        try:
            # Build comprehensive analysis prompt
            logger.info("📝 Building holistic analysis prompt with parent persona")
            analysis_prompt = build_video_analysis_prompt(
                child_data=child_data,
                extracted_data=extracted_data,
                analyst_context=analyst_context
            )

            # Analyze video with LLM
            logger.info("🤖 Sending video to LLM for analysis...")
            analysis_result = await self._analyze_with_llm(
                video_path=video_path,
                prompt=analysis_prompt
            )

            # Validate and parse result
            logger.info("✅ Validating analysis structure...")
            validated_result = self._validate_analysis(analysis_result)

            # Check if video validation failed
            if validated_result.get("_validation_failed"):
                # Video didn't pass validation - mark with special status
                validation_reason = validated_result.get("_validation_reason", ["Unknown validation failure"])
                recommendation = validated_result.get("_validation_recommendation", "request_new_video")

                logger.warning(f"⚠️ Video validation failed: {validation_reason}")

                # Still store the result (contains validation info) but mark status appropriately
                artifact.status = "validation_failed"
                artifact.content = json.dumps(validated_result, ensure_ascii=False)
                artifact.error_message = f"Video validation failed: {'; '.join(validation_reason)}"
                artifact.generation_duration_seconds = time.time() - start_time
                artifact.generation_model = getattr(self.llm_provider, "model_name", "unknown")

                logger.info(
                    f"⚠️ Video analysis complete but VALIDATION FAILED in {artifact.generation_duration_seconds:.2f}s "
                    f"for {child_name} - {guideline_title}. Recommendation: {recommendation}"
                )
            else:
                # Mark artifact as ready
                artifact.mark_ready(json.dumps(validated_result, ensure_ascii=False))
                artifact.generation_duration_seconds = time.time() - start_time
                artifact.generation_model = getattr(self.llm_provider, "model_name", "unknown")

                logger.info(
                    f"✅ Video analysis complete in {artifact.generation_duration_seconds:.2f}s "
                    f"for {child_name} - {guideline_title}"
                )

        except Exception as e:
            logger.error(f"❌ Error analyzing video: {e}", exc_info=True)
            artifact.mark_error(str(e))

        return artifact

    async def _analyze_with_llm(
        self,
        video_path: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Upload video to Gemini File API and analyze with comprehensive prompt.

        Uses Gemini's File API for videos (required for 3-5 minute videos).

        Process:
        1. Upload video using File API (async processing)
        2. Wait for processing to complete if needed
        3. Send analysis request with video reference + prompt
        4. Parse and return structured JSON result

        Args:
            video_path: Path to video file (MP4, MOV, AVI, etc.)
            prompt: Comprehensive holistic analysis system prompt

        Returns:
            Parsed JSON analysis result with 11 sections
        """
        import os
        from pathlib import Path

        logger.info(f"📤 Uploading video to Gemini File API: {video_path}")

        try:
            # Check if file exists
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # Get file info
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            logger.info(f"   File size: {file_size_mb:.2f} MB")

            # Upload video using Gemini File API
            # Note: This uses the genai client directly (not our wrapper)
            from google import genai

            # Get API key from environment
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment")

            client = genai.Client(api_key=api_key)

            # Upload file
            uploaded_file = client.files.upload(file=video_path)
            logger.info(f"✅ Video uploaded: {uploaded_file.name}")
            logger.info(f"   URI: {uploaded_file.uri}")
            logger.info(f"   State: {uploaded_file.state}")

            # Wait for processing if needed
            # Files are usually processed immediately, but check status
            import time
            max_wait = 30  # seconds
            wait_time = 0
            while uploaded_file.state == "PROCESSING" and wait_time < max_wait:
                logger.info(f"   Waiting for video processing... ({wait_time}s)")
                time.sleep(2)
                wait_time += 2
                # Refresh file status
                uploaded_file = client.files.get(name=uploaded_file.name)

            if uploaded_file.state != "ACTIVE":
                raise ValueError(f"Video processing failed or timed out. State: {uploaded_file.state}")

            logger.info(f"✅ Video ready for analysis")

            # Send analysis request with video + prompt + structured output schema
            logger.info("🤖 Sending video + prompt to Gemini for analysis...")

            from google.genai import types

            try:
                # CRITICAL: Disable AFC to prevent SDK from auto-executing any function calls
                # (even though we're not using function calling here, we want consistent behavior)
                response = client.models.generate_content(
                    model="gemini-3-pro-preview",  # Most current and capable model
                    contents=[
                        uploaded_file,  # Video file reference
                        prompt  # Analysis prompt (comes AFTER video as per best practices)
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.3,  # Lower temperature for structured analysis
                        max_output_tokens=8000,  # Comprehensive output needed
                        response_mime_type="application/json",  # Request JSON output
                        response_schema=get_video_analysis_schema(),  # Enforce structured output schema
                        # CRITICAL: Disable AFC even though not using functions
                        # This prevents the "AFC is enabled" log message and ensures consistent behavior
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True,
                            maximum_remote_calls=0  # Must be 0 to fully disable AFC
                        )
                    )
                )
            except Exception as api_error:
                # Handle Gemini API errors with helpful messages
                error_str = str(api_error).lower()

                if "invalid_argument" in error_str or "schema" in error_str:
                    # Schema validation error from Gemini
                    logger.error(f"❌ Schema validation error: {api_error}")
                    raise ValueError(
                        f"Video analysis schema validation failed. This is a configuration error, not an issue with your video. "
                        f"Details: {str(api_error)}"
                    )
                elif "400" in error_str or "404" in error_str or "500" in error_str:
                    # HTTP error from Gemini API
                    logger.error(f"❌ Gemini API error: {api_error}")
                    raise ValueError(
                        f"Error communicating with video analysis service. Please try again later. Details: {str(api_error)}"
                    )
                else:
                    # Re-raise unknown errors
                    raise

            logger.info("✅ Analysis response received")

            # ⚠️ CRITICAL: Extract text from parts, NOT response.text!
            # response.text concatenates ALL parts including thought_signature from Gemini 3 Pro,
            # which would contaminate our structured JSON output
            content = ""
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            # ⚠️ CRITICAL FIX: thought_signature is an ATTRIBUTE of the Part, not a separate part!
                            # The same Part can have BOTH part.text (user-facing JSON) and part.thought (internal reasoning).
                            # We want the TEXT (JSON) but not the thought.

                            # Extract text content (the JSON we need)
                            if hasattr(part, 'text') and part.text:
                                content += part.text
                                # Log if this part also has thought_signature (for debugging)
                                if hasattr(part, 'thought'):
                                    logger.debug("🧠 Part has thought_signature (ignored, text extracted)")

                            # If part has ONLY thought with NO text, skip it
                            elif hasattr(part, 'thought'):
                                logger.debug("🧠 Skipping part with ONLY thought_signature (no text)")
                                continue

            if not content:
                logger.error("❌ No text content in Gemini response!")
                raise ValueError("Gemini returned empty response for video analysis")

            # Try to parse as JSON
            try:
                result = json.loads(content)

                # If result is a list, get first item
                if isinstance(result, list) and len(result) > 0:
                    return result[0]

                return result

            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract from markdown
                logger.warning(f"Initial JSON parse failed, trying markdown extraction: {e}")

                import re
                # Strip markdown code blocks if present
                if "```json" in content:
                    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if match:
                        content = match.group(1)
                elif "```" in content:
                    match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                    if match:
                        content = match.group(1)

                result = json.loads(content)

                if isinstance(result, list) and len(result) > 0:
                    return result[0]

                return result

        except Exception as e:
            logger.error(f"❌ Error in video analysis with LLM: {e}", exc_info=True)
            raise

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis structure and ensure required fields.
        Also checks video_validation to determine if video is usable.

        Args:
            analysis: Raw analysis from LLM

        Returns:
            Validated and potentially augmented analysis
        """
        required_sections = [
            "analysis_metadata",
            "video_validation",  # NEW: Critical validation section
            "demographics",
            "task_context_analysis",
            "holistic_summary",
            "observed_strengths",
            "developmental_domains",
            "clinical_indicators_observed",
            "integration_with_parent_report",
            "evidence_video_clips",
            "limitations_and_disclaimer"
        ]

        missing_sections = [s for s in required_sections if s not in analysis]

        if missing_sections:
            logger.warning(f"⚠️ Analysis missing sections: {missing_sections}")
            # Log but don't fail - LLM might have used slightly different structure

        # Check video validation results
        video_validation = analysis.get("video_validation", {})
        if video_validation:
            is_usable = video_validation.get("is_usable", True)
            recommendation = video_validation.get("recommendation", "proceed_with_analysis")
            content_issues = video_validation.get("content_issues", [])

            # Log validation results
            scenario_match = video_validation.get("scenario_match", {})
            child_verification = video_validation.get("child_verification", {})

            if not is_usable:
                logger.error(f"❌ VIDEO VALIDATION FAILED!")
                logger.error(f"   - Recommendation: {recommendation}")
                logger.error(f"   - Issues: {content_issues}")
                logger.error(f"   - Scenario match: {scenario_match.get('matches_requested_scenario', 'unknown')}")
                logger.error(f"   - Child verification: {child_verification.get('appears_to_be_same_child', 'unknown')}")

                # Mark the analysis with validation failure
                analysis["_validation_failed"] = True
                analysis["_validation_reason"] = content_issues or ["Video did not pass validation"]
                analysis["_validation_recommendation"] = recommendation
            else:
                # Log successful validation
                logger.info(f"✅ Video validation passed")
                if not scenario_match.get("matches_requested_scenario", True):
                    logger.warning(f"   ⚠️ Scenario mismatch but continuing: {scenario_match.get('mismatch_reason', 'unknown')}")
                if not child_verification.get("appears_to_be_same_child", True):
                    logger.warning(f"   ⚠️ Child verification concern: {child_verification.get('verification_notes', 'unknown')}")

        # Ensure strengths are present (critical for holistic approach)
        if not analysis.get("observed_strengths"):
            logger.warning("⚠️ No strengths identified - this violates holistic approach!")

        return analysis

    async def analyze_multiple_videos(
        self,
        videos: list,
        child_data: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> Artifact:
        """
        Analyze multiple videos and generate cross-video patterns.

        Args:
            videos: List of video dicts with {path, analyst_context}
            child_data: Child demographics
            extracted_data: Full interview extraction

        Returns:
            Artifact with comprehensive multi-video analysis
        """
        artifact_id = "multi_video_analysis"
        start_time = time.time()

        child_name = child_data.get('name', 'Unknown')
        logger.info(f"🎬 Starting multi-video analysis for {child_name} ({len(videos)} videos)")

        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type="analysis",
            status="generating",
            content_format="json",
            generation_inputs={
                "child_name": child_name,
                "video_count": len(videos)
            }
        )

        try:
            # Analyze each video separately
            individual_analyses = []
            for idx, video in enumerate(videos):
                logger.info(f"   Analyzing video {idx + 1}/{len(videos)}: {video.get('guideline_title', 'Unknown')}")

                video_artifact = await self.analyze_video(
                    video_path=video['path'],
                    child_data=child_data,
                    extracted_data=extracted_data,
                    analyst_context=video['analyst_context'],
                    video_id=video.get('id', f'video_{idx}')
                )

                if video_artifact.status == "ready":
                    individual_analyses.append(json.loads(video_artifact.content))
                else:
                    logger.error(f"Failed to analyze video {idx + 1}: {video_artifact.error_message}")

            # Generate cross-video synthesis
            logger.info("🔗 Generating cross-video patterns and synthesis...")
            synthesis = await self._synthesize_multi_video(
                individual_analyses=individual_analyses,
                child_data=child_data,
                extracted_data=extracted_data
            )

            result = {
                "individual_analyses": individual_analyses,
                "cross_video_synthesis": synthesis,
                "analysis_metadata": {
                    "total_videos": len(videos),
                    "successful_analyses": len(individual_analyses),
                    "generation_date": datetime.now().isoformat(),
                    "child_name": child_name
                }
            }

            artifact.mark_ready(json.dumps(result, ensure_ascii=False))
            artifact.generation_duration_seconds = time.time() - start_time
            artifact.generation_model = getattr(self.llm_provider, "model_name", "unknown")

            logger.info(f"✅ Multi-video analysis complete in {artifact.generation_duration_seconds:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error in multi-video analysis: {e}", exc_info=True)
            artifact.mark_error(str(e))

        return artifact

    async def _synthesize_multi_video(
        self,
        individual_analyses: list,
        child_data: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate cross-video patterns and comprehensive synthesis.

        Args:
            individual_analyses: List of individual video analyses
            child_data: Child demographics
            extracted_data: Interview data

        Returns:
            Cross-video synthesis dict
        """
        # TODO: Implement comprehensive cross-video synthesis
        # This should identify:
        # - Consistent patterns across contexts
        # - Context-dependent behaviors
        # - Comprehensive strength profile
        # - Integrated clinical picture

        logger.info("📊 Cross-video synthesis not yet fully implemented - returning placeholder")

        return {
            "consistent_patterns": {
                "strengths_across_contexts": [],
                "challenges_across_contexts": [],
                "regulation_patterns": []
            },
            "context_dependent_behaviors": [],
            "comprehensive_recommendation": "Multi-video synthesis pending full implementation"
        }
