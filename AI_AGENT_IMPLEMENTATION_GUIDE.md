# AI Agent System Implementation Guide for Chitta

## Executive Summary

This document provides a comprehensive architectural blueprint for implementing an intelligent AI agent system within the Chitta application. The system transforms a traditional multi-step form-based workflow into a conversational, adaptive experience that removes cognitive burden from users while maintaining clinical rigor.

**Last Updated**: November 2, 2025
**Status**: Planning & Design Phase

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Agent Pipeline Analysis](#2-agent-pipeline-analysis)
3. [Frontend Architecture & State Management](#3-frontend-architecture--state-management)
4. [UI/UX Patterns & Component Design](#4-uiux-patterns--component-design)
5. [Backend Integration Strategy](#5-backend-integration-strategy)
6. [Real-time Processing & Streaming](#6-real-time-processing--streaming)
7. [Error Handling & Graceful Degradation](#7-error-handling--graceful-degradation)
8. [Testing & Validation Strategy](#8-testing--validation-strategy)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Security & Privacy Considerations](#10-security--privacy-considerations)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Conversation │  │   Context    │  │    Deep Views           │  │
│  │  Interface   │  │   Surface    │  │  (Reports, Experts)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    Application State Layer                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Agent State Manager (Zustand/Redux/Context)                 │  │
│  │  - Conversation State    - Video Upload State                │  │
│  │  - Interview Progress    - Analysis Results                  │  │
│  │  - UI State              - Report Generation State           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                      Service/API Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │ Conversation│  │    Video    │  │   Report    │  │  Expert  │  │
│  │   Service   │  │   Service   │  │  Service    │  │ Matching │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                        Backend AI Pipeline                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │  Agent 1:   │→ │  Agent 2:   │→ │  Agent 3:   │→ │ Agent 4: │  │
│  │ Interview   │  │  Interview  │  │    Video    │  │ Report   │  │
│  │ Conductor   │  │  Analyzer   │  │  Analyzer   │  │Generator │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Architectural Principles

**1. Progressive Disclosure**
- Reveal complexity gradually
- Show only what's needed at each step
- Adaptive UI based on user responses and AI analysis

**2. Intelligent State Management**
- Centralized agent state separate from UI state
- Predictable state transitions
- Ability to resume interrupted flows

**3. Optimistic UI Updates**
- Immediate feedback for user actions
- Background processing with streaming updates
- Graceful handling of backend delays

**4. Context-Aware Components**
- Components adapt based on interview stage
- Dynamic rendering based on AI analysis results
- Seamless transitions between conversation and structured views

---

## 2. Agent Pipeline Analysis

### 2.1 Agent 1: Interview Conductor

**Purpose**: Conduct empathetic, structured parent interview

**Key Capabilities**:
- Multi-stage conversation flow (5 stages)
- Natural language understanding of parent responses
- Dynamic question generation based on context
- Hebrew language support with RTL layout
- Emotional intelligence and empathy

**State Output**:
```typescript
interface InterviewState {
  currentStage: 1 | 2 | 3 | 4 | 5;
  conversationHistory: Message[];
  extractedData: {
    childDetails: ChildDetails;
    concerns: Concern[];
    strengths: Strength[];
    // ... more structured data
  };
  stageProgress: {
    stage1Complete: boolean;
    stage2Complete: boolean;
    stage3Complete: boolean;
    stage4Complete: boolean;
    stage5Complete: boolean;
  };
}
```

**Integration Points**:
- Real-time conversation UI
- Progress indicators
- Context cards showing extracted information
- Suggestions popup for quick responses

### 2.2 Agent 2: Interview Analyzer

**Purpose**: Transform conversation transcript into structured clinical data

**Input**: Raw conversation transcript
**Output**: Comprehensive JSON with:
- Child details
- Difficulties detailed with specific examples
- Medical/developmental history
- Family context
- Strengths and positives

**Processing Approach**:
- Runs after interview completion
- Can also run incrementally during interview for progressive data extraction
- Provides structured data for video filming instructions

**State Output**:
```typescript
interface InterviewSummary {
  child_details: ChildDetails;
  interview_summary: InterviewSummaryData;
  strengths_and_positives: Strengths;
  difficulties_detailed: Difficulty[];
  medical_developmental_history: MedicalHistory;
  // ... full structure from prompt
}
```

### 2.3 Agent 3: Video Analyzer

**Purpose**: Observe and analyze child behavior in video segments

**Input**:
- Video file(s)
- Interview summary JSON
- Child age/gender

**Output**: Detailed behavioral observations with:
- Observational metrics
- DSM-5 indicator mappings
- Comparison to parent interview
- Strengths observed in video

**Processing Considerations**:
- Video processing is computationally expensive
- May require async processing with status updates
- Multiple videos may need sequential or parallel processing

**State Output**:
```typescript
interface VideoAnalysis {
  child_id: string;
  observation_context_description: string;
  dsm5_adhd_indicators_observed: ADHD_Indicators;
  dsm5_asd_indicators_observed: ASD_Indicators;
  interview_data_comparison: Comparison;
  justification_evidence: Evidence[];
  // ... full structure from prompt
}
```

### 2.4 Agent 4 & 5: Report Generators

**Purpose**: Generate professional and parent-friendly reports

**Input**:
- Interview summary JSON
- Video analysis JSON

**Outputs**:
- Professional clinical report (Markdown + structured data)
- Parent-friendly report (empathetic Markdown)
- Visual indicator data for UI
- Expert recommendations

**Processing Approach**:
- Runs after video analysis complete
- Can generate both reports in parallel
- Provides structured data for expert matching

---

## 3. Frontend Architecture & State Management

### 3.1 State Management Architecture

**Recommendation**: Use **Zustand** for AI agent state management

**Why Zustand?**
- Lightweight and simple API
- No provider hell
- Built-in TypeScript support
- Easy to integrate with existing React components
- Supports middleware for persistence and devtools

### 3.2 Agent State Store Structure

```typescript
// stores/agentStore.ts
import create from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AgentState {
  // Interview State
  interview: {
    status: 'not_started' | 'in_progress' | 'completed' | 'error';
    currentStage: number;
    messages: Message[];
    extractedData: Partial<InterviewSummary>;
    isTyping: boolean;
    error: Error | null;
  };

  // Video Upload State
  videos: {
    status: 'not_started' | 'uploading' | 'processing' | 'completed' | 'error';
    uploadedVideos: VideoFile[];
    currentVideoIndex: number;
    analysisResults: VideoAnalysis[];
    error: Error | null;
  };

  // Report Generation State
  reports: {
    status: 'not_started' | 'generating' | 'completed' | 'error';
    professionalReport: ProfessionalReport | null;
    parentReport: ParentReport | null;
    visualIndicators: VisualIndicatorData | null;
    error: Error | null;
  };

  // Expert Matching State
  expertMatching: {
    status: 'not_started' | 'searching' | 'completed' | 'error';
    recommendations: ExpertRecommendation[];
    selectedExpert: Expert | null;
    error: Error | null;
  };

  // Actions
  startInterview: () => void;
  sendMessage: (message: string) => Promise<void>;
  completeStage: (stage: number) => void;
  uploadVideo: (file: File) => Promise<void>;
  generateReports: () => Promise<void>;
  searchExperts: () => Promise<void>;
  reset: () => void;
}

export const useAgentStore = create<AgentState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        interview: {
          status: 'not_started',
          currentStage: 0,
          messages: [],
          extractedData: {},
          isTyping: false,
          error: null,
        },
        videos: {
          status: 'not_started',
          uploadedVideos: [],
          currentVideoIndex: 0,
          analysisResults: [],
          error: null,
        },
        reports: {
          status: 'not_started',
          professionalReport: null,
          parentReport: null,
          visualIndicators: null,
          error: null,
        },
        expertMatching: {
          status: 'not_started',
          recommendations: [],
          selectedExpert: null,
          error: null,
        },

        // Actions implementation
        startInterview: () => {
          set((state) => ({
            interview: {
              ...state.interview,
              status: 'in_progress',
              currentStage: 1,
            },
          }));
        },

        sendMessage: async (message: string) => {
          const { interview } = get();

          // Add user message
          set((state) => ({
            interview: {
              ...state.interview,
              messages: [
                ...state.interview.messages,
                { sender: 'user', text: message, timestamp: Date.now() },
              ],
              isTyping: true,
            },
          }));

          try {
            // Call backend API
            const response = await conversationService.sendMessage(
              message,
              interview.currentStage,
              interview.messages
            );

            // Update state with AI response
            set((state) => ({
              interview: {
                ...state.interview,
                messages: [
                  ...state.interview.messages,
                  {
                    sender: 'chitta',
                    text: response.message,
                    timestamp: Date.now(),
                  },
                ],
                currentStage: response.stage,
                extractedData: {
                  ...state.interview.extractedData,
                  ...response.extractedData,
                },
                isTyping: false,
              },
            }));

            // Check for stage completion
            if (response.stageCompleted) {
              get().completeStage(response.stage);
            }
          } catch (error) {
            set((state) => ({
              interview: {
                ...state.interview,
                status: 'error',
                error: error as Error,
                isTyping: false,
              },
            }));
          }
        },

        completeStage: (stage: number) => {
          // Handle stage transitions
          // Show appropriate UI feedback
          // Update progress indicators
        },

        uploadVideo: async (file: File) => {
          set((state) => ({
            videos: { ...state.videos, status: 'uploading' },
          }));

          try {
            const uploadedVideo = await videoService.upload(file);

            set((state) => ({
              videos: {
                ...state.videos,
                status: 'processing',
                uploadedVideos: [...state.videos.uploadedVideos, uploadedVideo],
              },
            }));

            // Start analysis
            const analysis = await videoService.analyze(
              uploadedVideo.id,
              get().interview.extractedData
            );

            set((state) => ({
              videos: {
                ...state.videos,
                status: 'completed',
                analysisResults: [...state.videos.analysisResults, analysis],
              },
            }));
          } catch (error) {
            set((state) => ({
              videos: {
                ...state.videos,
                status: 'error',
                error: error as Error,
              },
            }));
          }
        },

        generateReports: async () => {
          set((state) => ({
            reports: { ...state.reports, status: 'generating' },
          }));

          try {
            const { interview, videos } = get();

            // Generate both reports in parallel
            const [professionalReport, parentReport] = await Promise.all([
              reportService.generateProfessionalReport(
                interview.extractedData,
                videos.analysisResults
              ),
              reportService.generateParentReport(
                interview.extractedData,
                videos.analysisResults
              ),
            ]);

            set((state) => ({
              reports: {
                ...state.reports,
                status: 'completed',
                professionalReport,
                parentReport,
                visualIndicators: professionalReport.visual_indicator_data,
              },
            }));
          } catch (error) {
            set((state) => ({
              reports: {
                ...state.reports,
                status: 'error',
                error: error as Error,
              },
            }));
          }
        },

        searchExperts: async () => {
          // Implementation for expert matching
        },

        reset: () => {
          set({
            interview: {
              status: 'not_started',
              currentStage: 0,
              messages: [],
              extractedData: {},
              isTyping: false,
              error: null,
            },
            videos: {
              status: 'not_started',
              uploadedVideos: [],
              currentVideoIndex: 0,
              analysisResults: [],
              error: null,
            },
            reports: {
              status: 'not_started',
              professionalReport: null,
              parentReport: null,
              visualIndicators: null,
              error: null,
            },
            expertMatching: {
              status: 'not_started',
              recommendations: [],
              selectedExpert: null,
              error: null,
            },
          });
        },
      }),
      {
        name: 'chitta-agent-storage',
        partialize: (state) => ({
          // Only persist essential data
          interview: {
            status: state.interview.status,
            currentStage: state.interview.currentStage,
            messages: state.interview.messages,
            extractedData: state.interview.extractedData,
          },
        }),
      }
    )
  )
);
```

### 3.3 Service Layer Implementation

```typescript
// services/conversationService.ts
export class ConversationService {
  private apiClient: ApiClient;

  async sendMessage(
    message: string,
    currentStage: number,
    conversationHistory: Message[]
  ): Promise<ConversationResponse> {
    const response = await this.apiClient.post('/api/conversation/message', {
      message,
      currentStage,
      conversationHistory,
    });

    return {
      message: response.data.message,
      stage: response.data.stage,
      stageCompleted: response.data.stageCompleted,
      extractedData: response.data.extractedData,
      contextCards: response.data.contextCards,
      suggestions: response.data.suggestions,
    };
  }

  async getVideoGuidelines(interviewSummary: InterviewSummary): Promise<string> {
    const response = await this.apiClient.post('/api/conversation/video-guidelines', {
      interviewSummary,
    });

    return response.data.guidelines;
  }
}

// services/videoService.ts
export class VideoService {
  private apiClient: ApiClient;

  async upload(file: File): Promise<UploadedVideo> {
    const formData = new FormData();
    formData.append('video', file);

    const response = await this.apiClient.post('/api/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        // Emit upload progress events
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        this.emitProgress(percentCompleted);
      },
    });

    return response.data;
  }

  async analyze(
    videoId: string,
    interviewSummary: InterviewSummary
  ): Promise<VideoAnalysis> {
    // Start analysis (async job)
    const job = await this.apiClient.post('/api/videos/analyze', {
      videoId,
      interviewSummary,
    });

    // Poll for completion or use WebSocket
    return this.pollAnalysisStatus(job.data.jobId);
  }

  private async pollAnalysisStatus(jobId: string): Promise<VideoAnalysis> {
    while (true) {
      const status = await this.apiClient.get(`/api/videos/analysis/${jobId}/status`);

      if (status.data.status === 'completed') {
        return status.data.result;
      } else if (status.data.status === 'failed') {
        throw new Error(status.data.error);
      }

      // Wait before next poll
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
}

// services/reportService.ts
export class ReportService {
  private apiClient: ApiClient;

  async generateProfessionalReport(
    interviewSummary: InterviewSummary,
    videoAnalyses: VideoAnalysis[]
  ): Promise<ProfessionalReport> {
    const response = await this.apiClient.post('/api/reports/professional', {
      interviewSummary,
      videoAnalyses,
    });

    return response.data;
  }

  async generateParentReport(
    interviewSummary: InterviewSummary,
    videoAnalyses: VideoAnalysis[]
  ): Promise<ParentReport> {
    const response = await this.apiClient.post('/api/reports/parent', {
      interviewSummary,
      videoAnalyses,
    });

    return response.data;
  }
}
```

---

## 4. UI/UX Patterns & Component Design

### 4.1 Adaptive Conversation Interface

The conversation interface must adapt based on interview stage and AI responses.

**Component Structure**:

```tsx
// components/AdaptiveConversation.tsx
import React, { useEffect, useRef } from 'react';
import { useAgentStore } from '../stores/agentStore';
import { ConversationTranscript } from './ConversationTranscript';
import { InputArea } from './InputArea';
import { SuggestionsPopup } from './SuggestionsPopup';
import { StageProgress } from './StageProgress';
import { ExtractedDataCards } from './ExtractedDataCards';

export const AdaptiveConversation: React.FC = () => {
  const {
    interview,
    sendMessage,
  } = useAgentStore();

  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const [suggestions, setSuggestions] = React.useState([]);

  // Auto-scroll to bottom on new messages
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [interview.messages]);

  // Generate suggestions based on current stage and context
  useEffect(() => {
    if (interview.currentStage > 0) {
      const stageSuggestions = getSuggestionsForStage(
        interview.currentStage,
        interview.extractedData
      );
      setSuggestions(stageSuggestions);
    }
  }, [interview.currentStage, interview.extractedData]);

  const handleSend = async (message: string) => {
    await sendMessage(message);
    setShowSuggestions(false);
  };

  const handleSuggestionClick = async (suggestion: string) => {
    await sendMessage(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-indigo-50 to-purple-50" dir="rtl">
      {/* Stage Progress Indicator */}
      <StageProgress
        currentStage={interview.currentStage}
        totalStages={5}
        className="sticky top-0 z-10"
      />

      {/* Conversation Area */}
      <div className="flex-1 overflow-y-auto p-4">
        <ConversationTranscript
          messages={interview.messages}
          isTyping={interview.isTyping}
        />

        {/* Dynamically show extracted data as context cards */}
        {interview.extractedData && Object.keys(interview.extractedData).length > 0 && (
          <ExtractedDataCards data={interview.extractedData} />
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
        <InputArea
          onSend={handleSend}
          onSuggestionsClick={() => setShowSuggestions(true)}
          disabled={interview.isTyping || interview.status === 'error'}
          placeholder="הקלד/י את תגובתך כאן..."
        />
      </div>

      {/* Suggestions Popup */}
      {showSuggestions && (
        <SuggestionsPopup
          suggestions={suggestions}
          onSuggestionClick={handleSuggestionClick}
          onClose={() => setShowSuggestions(false)}
        />
      )}
    </div>
  );
};

// Helper function to generate context-aware suggestions
function getSuggestionsForStage(
  stage: number,
  extractedData: Partial<InterviewSummary>
): Suggestion[] {
  // Logic to generate relevant suggestions based on:
  // 1. Current interview stage
  // 2. What data has been extracted so far
  // 3. Common responses for this stage

  const stageTemplates = {
    1: [
      { text: 'אני מוכן/ה להתחיל', icon: 'CheckCircle' },
      { text: 'יש לי שאלה לפני שנתחיל', icon: 'HelpCircle' },
    ],
    2: [
      { text: 'הוא/היא אוהב/ת לשחק בלגו', icon: 'Building' },
      { text: 'נהנה/ית מספרים וציורים', icon: 'Book' },
      { text: 'אוהב/ת לשחק בחוץ', icon: 'Sun' },
    ],
    3: [
      { text: 'קשיים בריכוז', icon: 'Focus' },
      { text: 'התפרצויות זעם', icon: 'AlertTriangle' },
      { text: 'קשיים חברתיים', icon: 'Users' },
    ],
    // ... more stages
  };

  return stageTemplates[stage] || [];
}
```

### 4.2 Progressive Data Extraction UI

As the AI extracts data during the interview, show it to the user in an unobtrusive way.

```tsx
// components/ExtractedDataCards.tsx
import React from 'react';
import { Baby, Calendar, Heart, AlertCircle } from 'lucide-react';

interface ExtractedDataCardsProps {
  data: Partial<InterviewSummary>;
}

export const ExtractedDataCards: React.FC<ExtractedDataCardsProps> = ({ data }) => {
  const cards = [];

  // Child details card
  if (data.child_details) {
    cards.push({
      id: 'child-details',
      icon: Baby,
      title: 'פרטי הילד/ה',
      content: (
        <div className="text-sm">
          {data.child_details.name && <p>שם: {data.child_details.name}</p>}
          {data.child_details.age_years && (
            <p>גיל: {data.child_details.age_years} שנים</p>
          )}
        </div>
      ),
      color: 'bg-blue-50 border-blue-200',
    });
  }

  // Strengths card
  if (data.strengths_and_positives?.child_likes_doing?.length > 0) {
    cards.push({
      id: 'strengths',
      icon: Heart,
      title: 'דברים שהילד/ה אוהב/ת',
      content: (
        <ul className="text-sm list-disc list-inside">
          {data.strengths_and_positives.child_likes_doing.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      ),
      color: 'bg-green-50 border-green-200',
    });
  }

  // Concerns card
  if (data.difficulties_detailed?.length > 0) {
    cards.push({
      id: 'concerns',
      icon: AlertCircle,
      title: 'תחומים לבדיקה',
      content: (
        <ul className="text-sm list-disc list-inside">
          {data.difficulties_detailed.map((difficulty, idx) => (
            <li key={idx}>{difficulty.area}</li>
          ))}
        </ul>
      ),
      color: 'bg-orange-50 border-orange-200',
    });
  }

  if (cards.length === 0) return null;

  return (
    <div className="my-4 space-y-2 animate-fadeIn">
      <p className="text-xs text-gray-500 text-center">מידע שנאסף עד כה:</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              className={`${card.color} border rounded-lg p-3 animate-slideUp`}
            >
              <div className="flex items-start gap-2">
                <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1">{card.title}</h4>
                  {card.content}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

### 4.3 Video Upload with Intelligent Guidance

```tsx
// components/VideoUploadFlow.tsx
import React, { useState } from 'react';
import { useAgentStore } from '../stores/agentStore';
import { Upload, Video, CheckCircle, AlertCircle } from 'lucide-react';

export const VideoUploadFlow: React.FC = () => {
  const {
    interview,
    videos,
    uploadVideo,
  } = useAgentStore();

  const [guidelines, setGuidelines] = useState<string>('');

  // Fetch video guidelines based on interview summary
  useEffect(() => {
    if (interview.status === 'completed') {
      conversationService
        .getVideoGuidelines(interview.extractedData as InterviewSummary)
        .then(setGuidelines);
    }
  }, [interview.status]);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await uploadVideo(file);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6" dir="rtl">
      {/* Guidelines Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">
          הנחיות לצילום וידאו
        </h2>

        <div
          className="prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{ __html: markdownToHtml(guidelines) }}
        />
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">העלאת סרטונים</h3>

        {/* Upload Button */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-500 transition-colors">
          <input
            type="file"
            accept="video/*"
            onChange={handleFileSelect}
            className="hidden"
            id="video-upload"
            disabled={videos.status === 'uploading' || videos.status === 'processing'}
          />
          <label
            htmlFor="video-upload"
            className="cursor-pointer flex flex-col items-center gap-3"
          >
            <Video className="w-12 h-12 text-indigo-500" />
            <span className="text-lg font-medium">
              לחץ/י לבחירת סרטון או גרור/י לכאן
            </span>
            <span className="text-sm text-gray-500">
              MP4, MOV, AVI - עד 500MB
            </span>
          </label>
        </div>

        {/* Upload Progress */}
        {videos.status === 'uploading' && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Upload className="w-5 h-5 text-blue-600 animate-bounce" />
              <span className="font-medium text-blue-900">מעלה סרטון...</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${videos.uploadProgress || 0}%` }}
              />
            </div>
          </div>
        )}

        {/* Processing Status */}
        {videos.status === 'processing' && (
          <div className="mt-4 bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
              <span className="font-medium text-purple-900">
                מנתח את הסרטון... זה עשוי לקחת מספר דקות
              </span>
            </div>
          </div>
        )}

        {/* Uploaded Videos List */}
        {videos.uploadedVideos.length > 0 && (
          <div className="mt-6 space-y-3">
            <h4 className="font-semibold text-gray-800">סרטונים שהועלו:</h4>
            {videos.uploadedVideos.map((video, idx) => (
              <div
                key={video.id}
                className="flex items-center justify-between bg-gray-50 rounded-lg p-3"
              >
                <div className="flex items-center gap-3">
                  <Video className="w-5 h-5 text-gray-600" />
                  <span className="text-sm">{video.filename}</span>
                </div>
                {videos.analysisResults[idx] ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
```

### 4.4 Intelligent Report Viewer

```tsx
// components/ReportViewer.tsx
import React, { useState } from 'react';
import { useAgentStore } from '../stores/agentStore';
import { FileText, Download, Share2, Eye } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export const ReportViewer: React.FC = () => {
  const { reports } = useAgentStore();
  const [activeTab, setActiveTab] = useState<'parent' | 'professional'>('parent');

  if (reports.status !== 'completed') {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-lg font-medium text-gray-700">מייצר דוחות...</p>
        </div>
      </div>
    );
  }

  const currentReport = activeTab === 'parent'
    ? reports.parentReport?.parent_report_markdown_hebrew
    : reports.professionalReport?.report_markdown_hebrew;

  return (
    <div className="max-w-5xl mx-auto p-6" dir="rtl">
      {/* Tab Selector */}
      <div className="bg-white rounded-t-lg shadow-md border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('parent')}
            className={`flex-1 px-6 py-4 font-semibold transition-colors ${
              activeTab === 'parent'
                ? 'bg-indigo-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <FileText className="w-5 h-5" />
              <span>דוח להורים</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('professional')}
            className={`flex-1 px-6 py-4 font-semibold transition-colors ${
              activeTab === 'professional'
                ? 'bg-indigo-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Eye className="w-5 h-5" />
              <span>דוח מקצועי</span>
            </div>
          </button>
        </div>
      </div>

      {/* Report Content */}
      <div className="bg-white rounded-b-lg shadow-md p-8">
        <div className="prose prose-sm max-w-none prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
          <ReactMarkdown>{currentReport}</ReactMarkdown>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-6 flex gap-3 justify-center">
        <button className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
          <Download className="w-5 h-5" />
          <span>הורדת PDF</span>
        </button>
        <button className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
          <Share2 className="w-5 h-5" />
          <span>שיתוף עם מומחה</span>
        </button>
      </div>

      {/* Visual Indicators Dashboard */}
      {reports.visualIndicators && (
        <div className="mt-8 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
          <h3 className="text-lg font-bold mb-4 text-gray-800">
            סיכום ויזואלי של הממצאים
          </h3>
          <VisualIndicatorsDashboard data={reports.visualIndicators} />
        </div>
      )}
    </div>
  );
};

// Visual Indicators Dashboard Component
interface VisualIndicatorsDashboardProps {
  data: VisualIndicatorData;
}

const VisualIndicatorsDashboard: React.FC<VisualIndicatorsDashboardProps> = ({ data }) => {
  const indicators = [
    { key: 'attention_indicator_level', label: 'קשב וריכוז' },
    { key: 'social_communication_indicator_level', label: 'תקשורת חברתית' },
    { key: 'hyperactivity_impulsivity_indicator_level', label: 'היפראקטיביות ואימפולסיביות' },
    { key: 'externalizing_behavior_indicator_level', label: 'התנהגויות מוחצנות' },
    { key: 'internalizing_behavior_indicator_level', label: 'התנהגויות מופנמות' },
  ];

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'high': return 'bg-red-500';
      case 'moderate': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-300';
    }
  };

  const getLevelText = (level: string) => {
    switch (level) {
      case 'high': return 'גבוה';
      case 'moderate': return 'בינוני';
      case 'low': return 'נמוך';
      default: return 'לא צוין';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {indicators.map((indicator) => {
        const level = data[indicator.key];
        return (
          <div key={indicator.key} className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                {indicator.label}
              </span>
              <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${getLevelColor(level)}`}>
                {getLevelText(level)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${getLevelColor(level)}`}
                style={{
                  width: level === 'high' ? '100%' : level === 'moderate' ? '60%' : '20%',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
```

---

## 5. Backend Integration Strategy

### 5.1 API Architecture

**Recommended Stack**:
- **Framework**: FastAPI (Python) or Express.js (Node.js)
- **AI/LLM Integration**: OpenAI API, Anthropic Claude, or Azure OpenAI
- **Video Processing**: FFmpeg + Cloud storage (AWS S3/Azure Blob)
- **Database**: PostgreSQL for structured data, MongoDB for JSON storage
- **Task Queue**: Celery (Python) or Bull (Node.js) for async jobs
- **Caching**: Redis for session management and caching

### 5.2 API Endpoints

```
POST /api/conversation/start
  - Initialize new interview session
  - Returns: sessionId, initialMessage

POST /api/conversation/message
  - Send user message, get AI response
  - Body: { sessionId, message, stage, history }
  - Returns: { message, stage, stageCompleted, extractedData, contextCards, suggestions }

POST /api/conversation/complete
  - Mark interview as complete
  - Trigger interview analysis (Agent 2)
  - Returns: { interviewSummary, videoGuidelines }

POST /api/videos/upload
  - Upload video file
  - Returns: { videoId, uploadUrl, status }

POST /api/videos/analyze
  - Start video analysis job (Agent 3)
  - Body: { videoId, interviewSummary, childAge, childGender }
  - Returns: { jobId, status }

GET /api/videos/analysis/:jobId/status
  - Poll for analysis job status
  - Returns: { status, progress, result? }

POST /api/reports/generate
  - Generate both reports (Agents 4 & 5)
  - Body: { interviewSummary, videoAnalyses[] }
  - Returns: { professionalReport, parentReport, visualIndicators }

POST /api/experts/search
  - Search for matching experts
  - Body: { professionalRecommendations, location?, preferences? }
  - Returns: { experts[] }

POST /api/experts/share-report
  - Share report with selected expert
  - Body: { expertId, reportType, permissions }
  - Returns: { shareId, shareUrl }
```

### 5.3 LLM Integration Pattern

```python
# backend/services/llm_service.py
from anthropic import Anthropic
from typing import Dict, List, Any
import json

class LLMService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def conduct_interview(
        self,
        user_message: str,
        current_stage: int,
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Agent 1: Interview Conductor
        """
        # Load system prompt (from your Prompt 1)
        system_prompt = self._load_interview_prompt()

        # Build messages array
        messages = self._build_messages(conversation_history, user_message)

        # Call Claude
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )

        # Parse response
        response_text = response.content[0].text

        # Extract stage identifier
        stage_match = re.search(r'\[CHITTA_CURRENT_STAGE: (\d+)\]', response_text)
        new_stage = int(stage_match.group(1)) if stage_match else current_stage

        # Check for completion tags
        stage_completed = any([
            '[CHITTA_STAGE_1_COMPLETED]' in response_text,
            '[CHITTA_STAGE_2_COMPLETED]' in response_text,
            '[CHITTA_STAGE_3_COMPLETED]' in response_text,
            '[CHITTA_STAGE_4_COMPLETED]' in response_text,
            '[CHITTA_INTERVIEW_CONCLUDED]' in response_text,
        ])

        # Remove tags from response
        clean_response = self._clean_response(response_text)

        # Extract structured data in real-time (optional progressive extraction)
        extracted_data = await self._extract_data_from_conversation(
            conversation_history + [{"role": "user", "content": user_message}]
        )

        # Generate context cards based on extracted data
        context_cards = self._generate_context_cards(extracted_data)

        # Generate suggestions for next response
        suggestions = self._generate_suggestions(new_stage, extracted_data)

        return {
            "message": clean_response,
            "stage": new_stage,
            "stageCompleted": stage_completed,
            "extractedData": extracted_data,
            "contextCards": context_cards,
            "suggestions": suggestions,
        }

    async def analyze_interview(
        self,
        transcript: str,
    ) -> Dict[str, Any]:
        """
        Agent 2: Interview Analyzer
        """
        system_prompt = self._load_analyzer_prompt()

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"להלן הטרנסקריפט:\n\n{transcript}"}
            ],
        )

        # Parse JSON from response
        response_text = response.content[0].text

        # Extract JSON (assumes response contains JSON)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            interview_summary = json.loads(json_match.group(0))
        else:
            raise ValueError("Failed to extract JSON from analyzer response")

        # Also extract video guidelines
        guidelines_match = re.search(
            r'<VIDEO_GUIDELINES>(.*?)</VIDEO_GUIDELINES>',
            response_text,
            re.DOTALL
        )
        video_guidelines = guidelines_match.group(1).strip() if guidelines_match else ""

        return {
            "interviewSummary": interview_summary,
            "videoGuidelines": video_guidelines,
        }

    async def analyze_video(
        self,
        video_path: str,
        interview_summary: Dict[str, Any],
        child_age: float,
        child_gender: str,
    ) -> Dict[str, Any]:
        """
        Agent 3: Video Analyzer
        Uses Claude with vision capability
        """
        # For video, we need to:
        # 1. Extract key frames or segments
        # 2. Send frames to Claude vision model
        # 3. Combine with interview summary for context

        # Extract frames (simplified)
        frames = await self._extract_video_frames(video_path, num_frames=10)

        # Encode frames as base64
        encoded_frames = [self._encode_frame(frame) for frame in frames]

        # Build prompt with interview summary
        system_prompt = self._load_video_analyzer_prompt(
            interview_summary_json=json.dumps(interview_summary, ensure_ascii=False),
            age=child_age,
            gender=child_gender,
        )

        # Create message with images
        content = [
            {
                "type": "text",
                "text": "נא לנתח את הווידאו הבא של הילד/ה:"
            }
        ]

        for encoded_frame in encoded_frames:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": encoded_frame,
                }
            })

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        )

        # Parse JSON response
        response_text = response.content[0].text
        video_analysis = json.loads(response_text)

        return video_analysis[0] if isinstance(video_analysis, list) else video_analysis

    async def generate_reports(
        self,
        interview_summary: Dict[str, Any],
        video_analyses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Agents 4 & 5: Report Generators
        """
        # Generate professional report
        professional_report = await self._generate_professional_report(
            interview_summary,
            video_analyses
        )

        # Generate parent report using data from professional report
        parent_report = await self._generate_parent_report(
            interview_summary,
            video_analyses,
            professional_report["professional_recommendations_data"],
            professional_report["visual_indicator_data"],
        )

        return {
            "professionalReport": professional_report,
            "parentReport": parent_report,
        }
```

---

## 6. Real-time Processing & Streaming

### 6.1 Streaming AI Responses

For a better UX, stream AI responses token-by-token instead of waiting for complete response.

```typescript
// services/conversationService.ts
export class ConversationService {
  async sendMessageStreaming(
    message: string,
    currentStage: number,
    conversationHistory: Message[],
    onChunk: (chunk: string) => void,
    onComplete: (data: ConversationResponse) => void
  ): Promise<void> {
    const response = await fetch('/api/conversation/message-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        currentStage,
        conversationHistory,
      }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    let buffer = '';
    let accumulatedText = '';

    while (true) {
      const { done, value } = await reader!.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process SSE chunks
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));

          if (data.type === 'chunk') {
            accumulatedText += data.text;
            onChunk(data.text);
          } else if (data.type === 'complete') {
            onComplete({
              message: accumulatedText,
              stage: data.stage,
              stageCompleted: data.stageCompleted,
              extractedData: data.extractedData,
              contextCards: data.contextCards,
              suggestions: data.suggestions,
            });
          }
        }
      }
    }
  }
}
```

**Backend SSE Implementation**:

```python
# backend/api/conversation.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

@app.post("/api/conversation/message-stream")
async def message_stream(request: ConversationRequest):
    async def generate():
        accumulated_text = ""

        # Stream from Claude
        async with anthropic_client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                accumulated_text += text

                # Send chunk to frontend
                yield f"data: {json.dumps({'type': 'chunk', 'text': text})}\n\n"

        # Process complete response
        stage, stage_completed, extracted_data = process_response(accumulated_text)

        # Send completion event
        yield f"data: {json.dumps({
            'type': 'complete',
            'stage': stage,
            'stageCompleted': stage_completed,
            'extractedData': extracted_data,
            'contextCards': generate_context_cards(extracted_data),
            'suggestions': generate_suggestions(stage, extracted_data),
        })}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 6.2 WebSocket for Long-Running Jobs

For video analysis and report generation, use WebSocket for real-time updates.

```typescript
// services/websocketService.ts
export class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, (data: any) => void> = new Map();

  connect(sessionId: string): void {
    this.ws = new WebSocket(`wss://api.chitta.com/ws/${sessionId}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      const listener = this.listeners.get(data.type);
      if (listener) {
        listener(data.payload);
      }
    };
  }

  on(eventType: string, callback: (data: any) => void): void {
    this.listeners.set(eventType, callback);
  }

  send(type: string, payload: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}

// Usage in component
useEffect(() => {
  const wsService = new WebSocketService();
  wsService.connect(sessionId);

  wsService.on('video_analysis_progress', (data) => {
    // Update progress bar
    setAnalysisProgress(data.progress);
  });

  wsService.on('video_analysis_complete', (data) => {
    // Update state with results
    setVideoAnalysis(data.result);
  });

  wsService.on('report_generation_progress', (data) => {
    setReportProgress(data.progress);
  });

  wsService.on('report_generation_complete', (data) => {
    setReports(data.reports);
  });

  return () => wsService.disconnect();
}, [sessionId]);
```

---

## 7. Error Handling & Graceful Degradation

### 7.1 Error Handling Patterns

```typescript
// stores/agentStore.ts - Enhanced error handling
export const useAgentStore = create<AgentState>()((set, get) => ({
  // ... state ...

  sendMessage: async (message: string) => {
    const { interview } = get();

    // Add user message immediately (optimistic UI)
    set((state) => ({
      interview: {
        ...state.interview,
        messages: [
          ...state.interview.messages,
          { sender: 'user', text: message, timestamp: Date.now() },
        ],
        isTyping: true,
        error: null, // Clear previous errors
      },
    }));

    try {
      const response = await conversationService.sendMessage(
        message,
        interview.currentStage,
        interview.messages
      );

      // Success path
      set((state) => ({
        interview: {
          ...state.interview,
          messages: [
            ...state.interview.messages,
            {
              sender: 'chitta',
              text: response.message,
              timestamp: Date.now(),
            },
          ],
          currentStage: response.stage,
          extractedData: {
            ...state.interview.extractedData,
            ...response.extractedData,
          },
          isTyping: false,
        },
      }));

      if (response.stageCompleted) {
        get().completeStage(response.stage);
      }
    } catch (error) {
      // Error handling with user-friendly messages
      const errorMessage = getErrorMessage(error);

      set((state) => ({
        interview: {
          ...state.interview,
          messages: [
            ...state.interview.messages,
            {
              sender: 'system',
              text: errorMessage,
              timestamp: Date.now(),
              isError: true,
            },
          ],
          isTyping: false,
          error: error as Error,
        },
      }));

      // Show retry option
      get().showRetryOption(message);
    }
  },

  showRetryOption: (originalMessage: string) => {
    set((state) => ({
      interview: {
        ...state.interview,
        retryMessage: originalMessage,
        showRetry: true,
      },
    }));
  },

  retry: async () => {
    const { interview } = get();
    if (interview.retryMessage) {
      set((state) => ({
        interview: {
          ...state.interview,
          showRetry: false,
        },
      }));
      await get().sendMessage(interview.retryMessage);
    }
  },
}));

// Error message mapper
function getErrorMessage(error: any): string {
  if (error.message?.includes('network')) {
    return 'נראה שיש בעיה בחיבור לאינטרנט. נסה/י שוב בעוד רגע.';
  }

  if (error.message?.includes('timeout')) {
    return 'הבקשה לקחה זמן רב מדי. נסה/י שוב.';
  }

  if (error.status === 429) {
    return 'קיבלנו הרבה בקשות. אנא המתן/י רגע ונסה/י שוב.';
  }

  if (error.status === 500) {
    return 'משהו השתבש בשרת שלנו. אנחנו עובדים על זה. נסה/י שוב בעוד כמה דקות.';
  }

  return 'משהו לא עבד כצפוי. נסה/י שוב או צור/י קשר עם התמיכה.';
}
```

### 7.2 Offline Support

```typescript
// services/offlineService.ts
export class OfflineService {
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    const request = indexedDB.open('ChittaOfflineDB', 1);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      // Create stores for offline data
      if (!db.objectStoreNames.contains('conversations')) {
        db.createObjectStore('conversations', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('drafts')) {
        db.createObjectStore('drafts', { keyPath: 'timestamp' });
      }
    };

    this.db = await new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async saveDraft(message: string, stage: number): Promise<void> {
    if (!this.db) return;

    const transaction = this.db.transaction(['drafts'], 'readwrite');
    const store = transaction.objectStore('drafts');

    await store.put({
      timestamp: Date.now(),
      message,
      stage,
    });
  }

  async loadDraft(): Promise<{ message: string; stage: number } | null> {
    if (!this.db) return null;

    const transaction = this.db.transaction(['drafts'], 'readonly');
    const store = transaction.objectStore('drafts');
    const request = store.getAll();

    return new Promise((resolve) => {
      request.onsuccess = () => {
        const drafts = request.result;
        resolve(drafts.length > 0 ? drafts[drafts.length - 1] : null);
      };
    });
  }

  async saveConversation(
    sessionId: string,
    conversation: ConversationState
  ): Promise<void> {
    if (!this.db) return;

    const transaction = this.db.transaction(['conversations'], 'readwrite');
    const store = transaction.objectStore('conversations');

    await store.put({
      id: sessionId,
      ...conversation,
      savedAt: Date.now(),
    });
  }
}

// Usage in store
const offlineService = new OfflineService();
await offlineService.init();

// Auto-save drafts
useEffect(() => {
  const interval = setInterval(() => {
    const { interview } = useAgentStore.getState();
    if (interview.messages.length > 0) {
      offlineService.saveConversation(sessionId, interview);
    }
  }, 30000); // Every 30 seconds

  return () => clearInterval(interval);
}, []);
```

---

## 8. Testing & Validation Strategy

### 8.1 Component Testing

```typescript
// __tests__/AdaptiveConversation.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AdaptiveConversation } from '../components/AdaptiveConversation';
import { useAgentStore } from '../stores/agentStore';

// Mock store
jest.mock('../stores/agentStore');

describe('AdaptiveConversation', () => {
  beforeEach(() => {
    (useAgentStore as jest.Mock).mockReturnValue({
      interview: {
        status: 'in_progress',
        currentStage: 1,
        messages: [
          {
            sender: 'chitta',
            text: 'שלום! אני Chitta.',
            timestamp: Date.now(),
          },
        ],
        isTyping: false,
        error: null,
      },
      sendMessage: jest.fn(),
    });
  });

  it('renders conversation messages', () => {
    render(<AdaptiveConversation />);
    expect(screen.getByText('שלום! אני Chitta.')).toBeInTheDocument();
  });

  it('sends message when user submits', async () => {
    const sendMessage = jest.fn();
    (useAgentStore as jest.Mock).mockReturnValue({
      interview: {
        status: 'in_progress',
        currentStage: 1,
        messages: [],
        isTyping: false,
      },
      sendMessage,
    });

    render(<AdaptiveConversation />);

    const input = screen.getByPlaceholderText('הקלד/י את תגובתך כאן...');
    const sendButton = screen.getByRole('button', { name: /שלח/i });

    await userEvent.type(input, 'היי');
    await userEvent.click(sendButton);

    expect(sendMessage).toHaveBeenCalledWith('היי');
  });

  it('shows typing indicator when AI is typing', () => {
    (useAgentStore as jest.Mock).mockReturnValue({
      interview: {
        status: 'in_progress',
        currentStage: 1,
        messages: [],
        isTyping: true,
      },
      sendMessage: jest.fn(),
    });

    render(<AdaptiveConversation />);
    expect(screen.getByTestId('typing-indicator')).toBeInTheDocument();
  });
});
```

### 8.2 Integration Testing with LLM

```python
# backend/tests/test_llm_service.py
import pytest
from services.llm_service import LLMService

@pytest.mark.asyncio
async def test_interview_conductor_stage_1():
    """Test that Agent 1 correctly handles stage 1 interactions"""
    llm_service = LLMService()

    # Simulate user starting interview
    response = await llm_service.conduct_interview(
        user_message="כן, אני מוכנה להתחיל",
        current_stage=1,
        conversation_history=[
            {"role": "assistant", "content": "האם זה בסדר מבחינתך שנתחיל?"}
        ],
    )

    # Assertions
    assert response["stage"] == 1
    assert "שם הילד" in response["message"] or "גיל" in response["message"]
    assert response["extractedData"] is not None

@pytest.mark.asyncio
async def test_interview_analyzer_extraction():
    """Test that Agent 2 correctly extracts structured data"""
    llm_service = LLMService()

    transcript = """
    Chitta: מה שם הילד שלך?
    הורה: שמו אורי.
    Chitta: ומה הגיל שלו?
    הורה: הוא בן 6 שנים ו-3 חודשים.
    Chitta: מה הקושי העיקרי?
    הורה: קשיים בריכוז, הוא לא יכול לשבת במקום.
    """

    result = await llm_service.analyze_interview(transcript)

    # Assertions
    assert result["interviewSummary"]["child_details"]["name"] == "אורי"
    assert result["interviewSummary"]["child_details"]["age_years"] == 6
    assert result["interviewSummary"]["child_details"]["age_months"] == 3
    assert len(result["interviewSummary"]["difficulties_detailed"]) > 0
    assert "קשב" in result["interviewSummary"]["difficulties_detailed"][0]["area"].lower()

@pytest.mark.asyncio
async def test_video_analyzer_indicators():
    """Test that Agent 3 identifies behavioral indicators"""
    llm_service = LLMService()

    # Use a test video
    video_path = "tests/fixtures/test_video_adhd_indicators.mp4"
    interview_summary = {
        "child_details": {"age_years": 6, "gender": "זכר"},
        "difficulties_detailed": [
            {"area": "קשב וריכוז", "description": "קשיים בריכוז"}
        ],
    }

    result = await llm_service.analyze_video(
        video_path,
        interview_summary,
        child_age=6.0,
        child_gender="זכר"
    )

    # Assertions
    assert "dsm5_adhd_indicators_observed" in result
    assert "attention_indicator_level" in result
    assert result["justification_evidence"] is not None
    assert len(result["justification_evidence"]) > 0
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)

**Week 1: State Management & Core Services**
- [ ] Set up Zustand store with agent state structure
- [ ] Create service layer (ConversationService, VideoService, ReportService)
- [ ] Implement API client with error handling
- [ ] Set up WebSocket service for real-time updates

**Week 2: Interview Flow (Agent 1)**
- [ ] Build AdaptiveConversation component
- [ ] Implement streaming message display
- [ ] Create StageProgress component
- [ ] Build ExtractedDataCards for progressive disclosure
- [ ] Integrate with backend Agent 1 API

**Week 3: Interview Analysis (Agent 2)**
- [ ] Implement interview completion flow
- [ ] Create interview analyzer backend integration
- [ ] Build VideoGuidelines display component
- [ ] Test full interview → analysis pipeline

### Phase 2: Video Processing (Weeks 4-6)

**Week 4: Video Upload**
- [ ] Build VideoUploadFlow component
- [ ] Implement file upload with progress tracking
- [ ] Create video preview and management UI
- [ ] Add video compression/optimization

**Week 5: Video Analysis (Agent 3)**
- [ ] Integrate video analysis API
- [ ] Implement async job polling/WebSocket updates
- [ ] Create analysis progress UI
- [ ] Build video observation results display

**Week 6: Testing & Optimization**
- [ ] Test video upload with various formats/sizes
- [ ] Optimize video processing pipeline
- [ ] Add error handling and retry logic
- [ ] Performance testing

### Phase 3: Report Generation (Weeks 7-9)

**Week 7: Report UI**
- [ ] Build ReportViewer component
- [ ] Implement professional/parent report tabs
- [ ] Create VisualIndicatorsDashboard
- [ ] Add PDF export functionality

**Week 8: Report Generation (Agents 4 & 5)**
- [ ] Integrate professional report generation API
- [ ] Integrate parent report generation API
- [ ] Implement report caching and versioning
- [ ] Add report sharing functionality

**Week 9: Expert Matching**
- [ ] Build expert search and matching UI
- [ ] Implement expert recommendation algorithm
- [ ] Create expert profile views
- [ ] Add secure report sharing with experts

### Phase 4: Polish & Launch (Weeks 10-12)

**Week 10: Testing & QA**
- [ ] End-to-end testing of full pipeline
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Security audit

**Week 11: Documentation & Training**
- [ ] Create user documentation
- [ ] Build onboarding flow
- [ ] Create demo videos
- [ ] Train support team

**Week 12: Launch Preparation**
- [ ] Staging environment deployment
- [ ] Load testing
- [ ] Monitoring and alerting setup
- [ ] Production deployment
- [ ] Post-launch monitoring

---

## 10. Security & Privacy Considerations

### 10.1 Data Privacy

**Principles**:
- End-to-end encryption for all personal data
- Minimal data collection (only what's necessary)
- User consent at each stage
- Right to deletion (GDPR compliance)
- Secure data storage with encryption at rest

**Implementation**:

```typescript
// services/encryptionService.ts
import CryptoJS from 'crypto-js';

export class EncryptionService {
  private key: string;

  constructor() {
    // In production, fetch from secure key management service
    this.key = process.env.REACT_APP_ENCRYPTION_KEY!;
  }

  encrypt(data: any): string {
    const jsonString = JSON.stringify(data);
    return CryptoJS.AES.encrypt(jsonString, this.key).toString();
  }

  decrypt(encryptedData: string): any {
    const bytes = CryptoJS.AES.decrypt(encryptedData, this.key);
    const decryptedString = bytes.toString(CryptoJS.enc.Utf8);
    return JSON.parse(decryptedString);
  }
}

// Usage in store
const encryptionService = new EncryptionService();

// Before sending to backend
const encryptedData = encryptionService.encrypt(interview.extractedData);

// When receiving from backend
const decryptedData = encryptionService.decrypt(response.data);
```

### 10.2 Authentication & Authorization

```typescript
// services/authService.ts
export class AuthService {
  async login(email: string, password: string): Promise<AuthToken> {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const { token, refreshToken } = await response.json();

    // Store tokens securely
    this.setTokens(token, refreshToken);

    return { token, refreshToken };
  }

  private setTokens(token: string, refreshToken: string): void {
    // Use httpOnly cookies for tokens (set by backend)
    // Or secure localStorage with encryption
    localStorage.setItem('auth_token', token);
    localStorage.setItem('refresh_token', refreshToken);
  }

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refresh_token');

    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });

    const { token } = await response.json();
    localStorage.setItem('auth_token', token);

    return token;
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  logout(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  }
}
```

### 10.3 Secure Video Upload

```typescript
// services/secureVideoService.ts
export class SecureVideoService extends VideoService {
  async uploadSecure(file: File): Promise<UploadedVideo> {
    // 1. Generate client-side encryption key
    const encryptionKey = await crypto.subtle.generateKey(
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );

    // 2. Read file as ArrayBuffer
    const arrayBuffer = await file.arrayBuffer();

    // 3. Encrypt file
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encryptedBuffer = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      encryptionKey,
      arrayBuffer
    );

    // 4. Create encrypted Blob
    const encryptedBlob = new Blob([encryptedBuffer], { type: 'application/octet-stream' });

    // 5. Upload encrypted file
    const formData = new FormData();
    formData.append('video', encryptedBlob, `${file.name}.encrypted`);
    formData.append('iv', btoa(String.fromCharCode(...iv)));

    const response = await this.apiClient.post('/api/videos/upload-secure', formData);

    // 6. Send encryption key to backend via separate secure channel
    const exportedKey = await crypto.subtle.exportKey('raw', encryptionKey);
    await this.apiClient.post('/api/videos/encryption-key', {
      videoId: response.data.videoId,
      key: btoa(String.fromCharCode(...new Uint8Array(exportedKey))),
    });

    return response.data;
  }
}
```

---

## Conclusion

This comprehensive guide provides the architectural foundation for implementing an intelligent AI agent system within the Chitta application. The key principles are:

1. **Progressive Enhancement**: Start with basic functionality, add AI intelligence incrementally
2. **User-Centric Design**: Remove cognitive burden through adaptive UI and smart defaults
3. **Robust Error Handling**: Graceful degradation and clear error messages
4. **Privacy First**: Encrypt sensitive data, minimal collection, user control
5. **Scalable Architecture**: Clean separation of concerns, modular services

The implementation should proceed in phases, with continuous testing and user feedback loops to ensure the AI system truly serves the users' needs and improves the experience of navigating the complex behavioral assessment process.

---

**Next Steps**:
1. Review this architecture with development team
2. Set up development environment
3. Begin Phase 1 implementation
4. Establish regular user testing sessions
5. Iterate based on feedback
