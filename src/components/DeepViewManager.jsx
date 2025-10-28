import React from 'react';
import ConsultationView from './deepviews/ConsultationView';
import DocumentUploadView from './deepviews/DocumentUploadView';
import DocumentListView from './deepviews/DocumentListView';
import ShareView from './deepviews/ShareView';
import JournalView from './deepviews/JournalView';
import ReportView from './deepviews/ReportView';
import ExpertProfileView from './deepviews/ExpertProfileView';
import VideoGalleryView from './deepviews/VideoGalleryView';
import VideoUploadView from './deepviews/VideoUploadView';
import FilmingInstructionView from './deepviews/FilmingInstructionView';
import DynamicGuidelineView from './deepviews/DynamicGuidelineView';
import MeetingSummaryView from './deepviews/MeetingSummaryView';

const viewComponents = {
  consultDoc: ConsultationView,
  uploadDoc: DocumentUploadView,
  viewDocs: DocumentListView,
  shareExpert: ShareView,
  journal: JournalView,
  parentReport: ReportView,
  proReport: ReportView,
  expert1: ExpertProfileView,
  expert2: ExpertProfileView,
  videoGallery: VideoGalleryView,
  upload: VideoUploadView,  // Changed from DocumentUploadView to VideoUploadView
  view1: FilmingInstructionView,
  view2: FilmingInstructionView,
  view3: FilmingInstructionView,
  summary: MeetingSummaryView,
  instructions: FilmingInstructionView,
  experts: ExpertProfileView,
  moreExperts: ExpertProfileView,
  dynamic_guideline: DynamicGuidelineView,  // New dynamic view for backend guidelines
};

export default function DeepViewManager({
  activeView,
  onClose,
  viewData,
  videos,
  journalEntries,
  onCreateJournalEntry,
  onDeleteJournalEntry,
  onCreateVideo,
  onDeleteVideo
}) {
  if (!activeView) return null;

  const ViewComponent = viewComponents[activeView];

  if (!ViewComponent) {
    console.warn(`No component found for view: ${activeView}`);
    return null;
  }

  // For dynamic_guideline, pass the viewData directly as data prop
  // For other views, pass as viewData
  const dataProps = activeView === 'dynamic_guideline'
    ? { data: viewData }
    : { data: viewData };

  return (
    <ViewComponent
      viewKey={activeView}
      onClose={onClose}
      {...dataProps}
      videos={videos}
      journalEntries={journalEntries}
      onCreateJournalEntry={onCreateJournalEntry}
      onDeleteJournalEntry={onDeleteJournalEntry}
      onCreateVideo={onCreateVideo}
      onDeleteVideo={onDeleteVideo}
    />
  );
}
