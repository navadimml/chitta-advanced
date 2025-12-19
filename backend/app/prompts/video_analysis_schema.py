"""
Video Analysis Schema - Structured Output Definition

Defines the JSON schema for Gemini's structured output feature.
Ensures the LLM returns properly formatted 11-section analysis.
"""

from google.genai import types


def get_video_analysis_schema() -> types.Schema:
    """
    Get the complete schema for holistic video analysis structured output.

    Returns:
        types.Schema object for Gemini's generate_content config
    """
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            # 0. Analysis Metadata
            "analysis_metadata": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "video_assignment": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "clinical_goal": types.Schema(type=types.Type.STRING),
                            "guideline_title": types.Schema(type=types.Type.STRING),
                            "parent_instruction_summary": types.Schema(type=types.Type.STRING),
                            "analytical_lens_applied": types.Schema(type=types.Type.STRING)
                        },
                        required=["clinical_goal", "guideline_title"]
                    ),
                    "parent_context": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "emotional_vibe": types.Schema(type=types.Type.STRING),
                            "vocabulary_used_in_analysis": types.Schema(
                                type=types.Type.STRING,
                                description="Hebrew terms and vocabulary used to describe child's behaviors"
                            ),
                            "context_assets_referenced": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(type=types.Type.STRING),
                                description="Specific toys, people, places from interview that appear in video"
                            )
                        }
                    ),
                    "observation_quality": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "video_clarity": types.Schema(type=types.Type.STRING),
                            "duration_adequacy": types.Schema(type=types.Type.STRING),
                            "context_richness": types.Schema(type=types.Type.STRING)
                        }
                    )
                },
                required=["video_assignment", "parent_context", "observation_quality"]
            ),

            # Video Validation - CRITICAL: Check video matches expected content
            "video_validation": types.Schema(
                type=types.Type.OBJECT,
                description="Validates the uploaded video matches the expected scenario and child",
                properties={
                    "is_usable": types.Schema(
                        type=types.Type.BOOLEAN,
                        description="Whether the video can be used for analysis (True if valid)"
                    ),
                    "scenario_match": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "matches_requested_scenario": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="Does video content match the filming instructions?"
                            ),
                            "what_was_requested": types.Schema(type=types.Type.STRING),
                            "what_video_shows": types.Schema(type=types.Type.STRING),
                            "match_confidence": types.Schema(
                                type=types.Type.STRING,
                                description="High/Medium/Low confidence the video matches"
                            ),
                            "mismatch_reason": types.Schema(
                                type=types.Type.STRING,
                                description="If mismatch, explain what's different"
                            )
                        },
                        required=["matches_requested_scenario", "what_video_shows", "match_confidence"]
                    ),
                    "child_verification": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "child_visible": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="Is a child clearly visible in the video?"
                            ),
                            "estimated_age_range": types.Schema(
                                type=types.Type.STRING,
                                description="Estimated age range of child in video (e.g., '2-4 years')"
                            ),
                            "age_consistent_with_profile": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="Does estimated age match the child's profile age?"
                            ),
                            "gender_consistent_with_profile": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="Does apparent gender match the child's profile?"
                            ),
                            "appears_to_be_same_child": types.Schema(
                                type=types.Type.BOOLEAN,
                                description="Does this appear to be the child discussed in the interview?"
                            ),
                            "verification_notes": types.Schema(
                                type=types.Type.STRING,
                                description="Any concerns about child identity or age mismatch"
                            )
                        },
                        required=["child_visible", "age_consistent_with_profile", "appears_to_be_same_child"]
                    ),
                    "content_issues": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="List of issues: wrong child, wrong scenario, empty video, unusable quality, etc."
                    ),
                    "recommendation": types.Schema(
                        type=types.Type.STRING,
                        description="proceed_with_analysis | request_new_video | partial_analysis_possible"
                    )
                },
                required=["is_usable", "scenario_match", "child_verification", "recommendation"]
            ),

            # Demographics
            "child_id": types.Schema(type=types.Type.STRING),
            "demographics": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(type=types.Type.STRING),
                    "age_years": types.Schema(type=types.Type.INTEGER),
                    "age_months": types.Schema(type=types.Type.INTEGER),
                    "gender": types.Schema(type=types.Type.STRING),
                    "age_gender_estimated": types.Schema(type=types.Type.BOOLEAN)
                },
                required=["name", "age_years", "gender"]
            ),

            # 1. Task Context Analysis
            "task_context_analysis": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "assigned_task": types.Schema(type=types.Type.STRING),
                    "actual_observation": types.Schema(type=types.Type.STRING),
                    "task_compliance_level": types.Schema(type=types.Type.STRING),
                    "environment_demand_level": types.Schema(type=types.Type.STRING),
                    "demand_elements": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "cognitive_demand": types.Schema(type=types.Type.STRING),
                            "social_demand": types.Schema(type=types.Type.STRING),
                            "sensory_demand": types.Schema(type=types.Type.STRING),
                            "emotional_demand": types.Schema(type=types.Type.STRING)
                        }
                    )
                },
                required=["assigned_task", "actual_observation", "task_compliance_level"]
            ),

            # 2. Holistic Summary
            "holistic_summary": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "temperament_and_personality": types.Schema(type=types.Type.STRING),
                    "energy_and_regulation_vibe": types.Schema(type=types.Type.STRING),
                    "preferred_learning_modalities": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    ),
                    "parent_child_dynamic_observed": types.Schema(type=types.Type.STRING),
                    "child_in_context_narrative": types.Schema(type=types.Type.STRING)
                },
                required=["temperament_and_personality", "energy_and_regulation_vibe"]
            ),

            # 3. Observed Strengths (MANDATORY)
            "observed_strengths": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "social_emotional_strengths": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "strength": types.Schema(type=types.Type.STRING),
                                "evidence_timestamp": types.Schema(type=types.Type.STRING),
                                "clinical_value": types.Schema(type=types.Type.STRING)
                            },
                            required=["strength", "evidence_timestamp", "clinical_value"]
                        )
                    ),
                    "cognitive_play_strengths": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "strength": types.Schema(type=types.Type.STRING),
                                "evidence_timestamp": types.Schema(type=types.Type.STRING),
                                "clinical_value": types.Schema(type=types.Type.STRING)
                            }
                        )
                    ),
                    "adaptive_strengths": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "strength": types.Schema(type=types.Type.STRING),
                                "evidence_timestamp": types.Schema(type=types.Type.STRING),
                                "clinical_value": types.Schema(type=types.Type.STRING)
                            }
                        )
                    ),
                    "unique_interests_abilities": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    )
                },
                required=["social_emotional_strengths", "cognitive_play_strengths", "adaptive_strengths"]
            ),

            # 4. Developmental Domains
            "developmental_domains": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "social_communication": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "eye_contact": types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "percentage_estimate": types.Schema(type=types.Type.NUMBER),
                                    "quality": types.Schema(type=types.Type.STRING),
                                    "contextual_variation": types.Schema(type=types.Type.STRING)
                                }
                            ),
                            "joint_attention": types.Schema(
                                type=types.Type.STRING,
                                description="Joint attention patterns observed"
                            ),
                            "gestural_communication": types.Schema(
                                type=types.Type.STRING,
                                description="Gestural communication patterns"
                            ),
                            "pragmatic_language": types.Schema(
                                type=types.Type.STRING,
                                description="Pragmatic language use observed"
                            )
                        }
                    ),
                    "play_complexity_profile": types.Schema(
                        type=types.Type.STRING,
                        description="Play complexity and developmental level"
                    ),
                    "regulation_and_sensory": types.Schema(
                        type=types.Type.STRING,
                        description="Regulation and sensory processing patterns"
                    ),
                    "executive_function_and_attention": types.Schema(
                        type=types.Type.STRING,
                        description="Executive function and attention observations"
                    ),
                    "motor_skills_brief": types.Schema(
                        type=types.Type.STRING,
                        description="Brief motor skills observations"
                    )
                }
            ),

            # 5. Clinical Indicators
            "clinical_indicators_observed": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "neurodevelopmental_patterns": types.Schema(
                        type=types.Type.STRING,
                        description="Neurodevelopmental patterns observed"
                    ),
                    "executive_function_challenges": types.Schema(
                        type=types.Type.STRING,
                        description="Executive function challenges observed"
                    ),
                    "externalizing_behaviors": types.Schema(
                        type=types.Type.STRING,
                        description="Externalizing behaviors observed"
                    ),
                    "internalizing_behaviors": types.Schema(
                        type=types.Type.STRING,
                        description="Internalizing behaviors observed"
                    ),
                    "language_communication": types.Schema(
                        type=types.Type.STRING,
                        description="Language and communication patterns"
                    )
                }
            ),

            # 6. Contextual Patterns
            "contextual_patterns": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "behavior_across_demand_levels": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "low_demand": types.Schema(type=types.Type.STRING),
                            "moderate_demand": types.Schema(type=types.Type.STRING),
                            "high_demand": types.Schema(type=types.Type.STRING)
                        }
                    ),
                    "triggers_and_escalation": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="Behavioral triggers and escalation patterns"
                    ),
                    "optimal_conditions_for_success": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    )
                }
            ),

            # 7. Integration with Parent Report
            "integration_with_parent_report": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "confirmations": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "parent_concern": types.Schema(type=types.Type.STRING),
                                "video_observation_data": types.Schema(type=types.Type.STRING),
                                "relevance": types.Schema(type=types.Type.STRING),
                                "clinical_significance": types.Schema(type=types.Type.STRING)
                            }
                        )
                    ),
                    "discrepancies": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="Discrepancies between parent report and video observations"
                    ),
                    "focus_point_findings": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "focus_question": types.Schema(type=types.Type.STRING),
                                "finding": types.Schema(type=types.Type.STRING),
                                "clinical_implication": types.Schema(type=types.Type.STRING),
                                "confidence_level": types.Schema(type=types.Type.STRING)
                            },
                            required=["focus_question", "finding"]
                        )
                    ),
                    "new_insights_not_in_parent_report": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="New insights observed in video that weren't mentioned in parent report"
                    )
                }
            ),

            # 8. Clinical Integration
            "clinical_integration": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "strength_based_pathways": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "identified_strength": types.Schema(type=types.Type.STRING),
                                "related_challenge": types.Schema(type=types.Type.STRING),
                                "bridge_strategy": types.Schema(type=types.Type.STRING),
                                "example": types.Schema(type=types.Type.STRING)
                            }
                        )
                    ),
                    "regulation_profile_summary": types.Schema(
                        type=types.Type.STRING,
                        description="Summary of child's regulation and sensory processing profile"
                    )
                }
            ),

            # 9. Preliminary Recommendations
            "preliminary_recommendations": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "immediate_parent_strategies": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="Immediate strategies parents can implement"
                    ),
                    "environmental_modifications": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    ),
                    "further_assessment_needed": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="Areas requiring further professional assessment"
                    ),
                    "follow_up_observation_targets": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    )
                }
            ),

            # 10. Evidence Video Clips (MM:SS timestamps)
            "evidence_video_clips": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "start_time": types.Schema(type=types.Type.STRING, description="MM:SS format"),
                        "end_time": types.Schema(type=types.Type.STRING, description="MM:SS format"),
                        "category": types.Schema(type=types.Type.STRING),
                        "subcategory": types.Schema(type=types.Type.STRING),
                        "description_of_behavior": types.Schema(type=types.Type.STRING),
                        "clinical_significance": types.Schema(type=types.Type.STRING),
                        "links_to_parent_report": types.Schema(type=types.Type.STRING),
                        "demonstrates_strength": types.Schema(type=types.Type.BOOLEAN),
                        "keyframe_description": types.Schema(type=types.Type.STRING)
                    },
                    required=["start_time", "end_time", "category", "description_of_behavior"]
                )
            ),

            # 11. Confidence & Limitations
            "analysis_confidence": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "overall_confidence": types.Schema(type=types.Type.STRING),
                    "domain_confidence_scores": types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "social_communication": types.Schema(type=types.Type.NUMBER),
                            "regulation_sensory": types.Schema(type=types.Type.NUMBER),
                            "executive_function": types.Schema(type=types.Type.NUMBER),
                            "play_development": types.Schema(type=types.Type.NUMBER)
                        }
                    ),
                    "factors_affecting_confidence": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    )
                }
            ),

            "limitations_and_disclaimer": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "limitations": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING)
                    ),
                    "context_specific_notes": types.Schema(type=types.Type.STRING),
                    "DISCLAIMER": types.Schema(type=types.Type.STRING)
                },
                required=["limitations", "DISCLAIMER"]
            )
        },
        required=[
            "analysis_metadata",
            "video_validation",  # CRITICAL: Must be filled first to check video validity
            "demographics",
            "task_context_analysis",
            "holistic_summary",
            "observed_strengths",
            "developmental_domains",
            "integration_with_parent_report",
            "evidence_video_clips",
            "limitations_and_disclaimer"
        ]
    )
