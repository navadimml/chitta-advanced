"""
Simulated Graphiti Client
מדמה Graphiti ללא Neo4j אמיתי - הכל ב-memory
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class SimulatedGraphitiClient:
    """
    Client מדומה ל-Graphiti
    שומר הכל ב-memory - מושלם לפיתוח!
    """

    def __init__(self):
        # Storage: group_id -> list of episodes
        self.episodes = defaultdict(list)

        # Index for fast search: group_id -> {word -> episodes}
        self.search_index = defaultdict(lambda: defaultdict(list))

        logger.info("✅ Simulated Graphiti initialized (in-memory)")

    async def initialize(self):
        """אתחול - לא צריך בגרסה מדומה"""
        pass

    async def add_episode(
        self,
        name: str,
        episode_body: Dict[str, Any],
        group_id: str,
        reference_time: Optional[datetime] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """הוספת episode - פשוט שומר ב-memory"""
        if reference_time is None:
            reference_time = datetime.now()

        episode = {
            "name": name,
            "body": episode_body,
            "group_id": group_id,
            "reference_time": reference_time,
            "created_at": datetime.now()
        }

        # שמירה
        self.episodes[group_id].append(episode)

        # אינדוקס לחיפוש
        self._index_episode(episode)

        logger.info(f"📝 Episode '{name}' added to group '{group_id}'")

        return {"status": "success", "episode_id": len(self.episodes[group_id]) - 1}

    def _index_episode(self, episode: Dict[str, Any]):
        """יצירת אינדקס לחיפוש מהיר"""
        group_id = episode["group_id"]
        body = episode["body"]

        # חלץ טקסט מכל השדות
        text_content = self._extract_text(body)

        # אינדקס לפי מילים
        words = set(text_content.lower().split())
        for word in words:
            if len(word) > 2:  # רק מילים באורך 3+
                self.search_index[group_id][word].append(episode)

    def _extract_text(self, obj: Any) -> str:
        """חילוץ כל הטקסט מאובייקט (רקורסיבי)"""
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            texts = []
            for v in obj.values():
                texts.append(self._extract_text(v))
            return " ".join(texts)
        elif isinstance(obj, list):
            texts = []
            for item in obj:
                texts.append(self._extract_text(item))
            return " ".join(texts)
        else:
            return str(obj)

    def get_all_episodes(self, group_id: str) -> List[Any]:
        """קבלת כל ה-episodes של קבוצה"""
        if group_id not in self.episodes:
            return []

        return [SimulatedSearchResult(episode) for episode in self.episodes[group_id]]

    async def search(
        self,
        query: str,
        group_id: str,
        center_node_uuid: Optional[str] = None,
        num_results: int = 20,
        reference_time: Optional[datetime] = None
    ) -> List[Any]:
        """חיפוש פשוט - מחפש במילים"""
        if group_id not in self.episodes:
            return []

        # מקרה מיוחד: שאילתות "all" מחזירות הכל
        if "all" in query.lower() or query.strip() == "*":
            results = self.episodes[group_id][:num_results]
            formatted_results = []
            for episode in results:
                formatted_results.append(SimulatedSearchResult(episode))
            logger.debug(f"🔍 Search '{query[:30]}...' (all) returned {len(formatted_results)} results")
            return formatted_results

        # פירוק השאילתה למילים
        query_words = set(query.lower().split())

        # חיפוש episodes עם מילים תואמות
        matched_episodes = []
        scores = {}

        for episode in self.episodes[group_id]:
            # ספירת התאמות
            episode_id = id(episode)
            score = 0

            episode_text = self._extract_text(episode["body"]).lower()

            for word in query_words:
                if len(word) > 2 and word in episode_text:
                    score += episode_text.count(word)

            if score > 0:
                matched_episodes.append(episode)
                scores[episode_id] = score

        # מיון לפי score
        matched_episodes.sort(key=lambda e: scores[id(e)], reverse=True)

        # החזרת top results
        results = matched_episodes[:num_results]

        # המרה לפורמט דומה ל-Graphiti אמיתי
        formatted_results = []
        for episode in results:
            formatted_results.append(SimulatedSearchResult(episode))

        logger.debug(f"🔍 Search '{query[:30]}...' returned {len(formatted_results)} results")

        return formatted_results

    async def close(self):
        """סגירה - לא צריך בגרסה מדומה"""
        logger.info("Simulated Graphiti closed")


class SimulatedSearchResult:
    """תוצאת חיפוש מדומה - מחקה את Graphiti אמיתי"""

    def __init__(self, episode: Dict[str, Any]):
        self.episode = episode
        self.body = episode["body"]
        self.reference_time = episode["reference_time"]
        self.name = episode.get("name", "")

        # ניסיון לחלץ entity_type
        if "concerns" in str(self.body):
            self.entity_type = "Concern"
        elif "strengths" in str(self.body):
            self.entity_type = "Strength"
        elif "behavioral_indicators" in str(self.body):
            self.entity_type = "BehavioralIndicator"
        elif "scenarios" in str(self.body):
            self.entity_type = "VideoGuideline"
        else:
            self.entity_type = "Episode"

        # שדה fact/description
        self.fact = self._extract_fact()
        self.description = self.fact

    def _extract_fact(self) -> str:
        """חילוץ עובדה ייצוגית"""
        if isinstance(self.body, dict):
            # נסה למצוא description או content
            for key in ["description", "content", "summary", "key_findings"]:
                if key in self.body:
                    return str(self.body[key])

            # אחרת - הטקסט הראשון שנמצא
            for v in self.body.values():
                if isinstance(v, str) and len(v) > 10:
                    return v[:200]

        return str(self.body)[:200]

    def __getattr__(self, name):
        """גישה דינמית לשדות"""
        if name in self.body:
            return self.body[name]
        return None
