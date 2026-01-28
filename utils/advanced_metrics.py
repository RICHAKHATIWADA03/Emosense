"""Advanced interview metrics calculator"""
import numpy as np
from collections import Counter
import config

class AdvancedMetricsCalculator:
    def __init__(self):
        pass
    
    def calculate_all_metrics(self, results):
        """Calculate all advanced metrics"""
        metrics = {}
        
        # Get emotion probabilities - handle both video (fusion) and audio (combined)
        if 'fusion' in results:
            fusion_probs = results['fusion']['probabilities']
        elif 'combined' in results:
            fusion_probs = results['combined']['probabilities']
        else:
            # Fallback
            fusion_probs = {e: 1.0/7 for e in config.EMOTION_LABELS}
        
        # 1. Engagement Score (0-100)
        metrics['engagement'] = self._calculate_engagement(fusion_probs, results)
        
        # 2. Stress/Nervousness Level (0-100)
        metrics['stress'] = self._calculate_stress(fusion_probs, results)
        
        # 3. Confidence Score (0-100)
        metrics['confidence'] = self._calculate_confidence(fusion_probs, results)
        
        # 4. Emotional Stability (0-100)
        metrics['stability'] = self._calculate_stability(results)
        
        # 5. Positivity Score (0-100)
        metrics['positivity'] = self._calculate_positivity(fusion_probs)
        
        # 6. Communication Quality (0-100)
        metrics['communication'] = self._calculate_communication(results)
        
        # 7. Overall Performance (0-100)
        metrics['overall'] = self._calculate_overall(metrics)
        
        # Add recommendations
        metrics['recommendations'] = self._generate_recommendations(metrics)
        
        return metrics
    
    def _calculate_engagement(self, probs, results):
        """Calculate engagement based on happy, surprise, neutral balance"""
        # High engagement: happy + surprise, moderate neutral
        engagement = (
            probs.get('happy', 0) * 1.5 +
            probs.get('surprise', 0) * 1.2 +
            probs.get('neutral', 0) * 0.3 -
            probs.get('sad', 0) * 0.5
        )
        
        # Boost if good face detection (only for video)
        if results.get('detection_rate', 0) > 0.8:
            engagement *= 1.1
        
        return min(100, max(0, engagement * 100))
    
    def _calculate_stress(self, probs, results):
        """Calculate stress level based on fear, anger, sad"""
        stress = (
            probs.get('fear', 0) * 2.0 +
            probs.get('angry', 0) * 1.5 +
            probs.get('sad', 0) * 1.0 +
            probs.get('disgust', 0) * 0.8
        )
        
        # Check for speech patterns indicating stress
        transcript = results.get('transcript', {}).get('text', '')
        stress_words = ['um', 'uh', 'like', 'you know', 'i mean', 'actually']
        word_count = len(transcript.split())
        if word_count > 0:
            stress_word_ratio = sum(transcript.lower().count(w) for w in stress_words) / word_count
            stress += stress_word_ratio * 0.3
        
        return min(100, max(0, stress * 100))
    
    def _calculate_confidence(self, probs, results):
        """Calculate confidence based on emotion certainty and posture"""
        # Higher confidence if emotions are clear (not all neutral)
        max_prob = max(probs.values())
        entropy = -sum(p * np.log(p + 1e-10) for p in probs.values() if p > 0)
        max_entropy = np.log(len(probs))
        
        confidence = (
            max_prob * 50 +  # Clear emotion = confidence
            (1 - entropy / max_entropy) * 30 +  # Low entropy = confident
            probs.get('happy', 0) * 20  # Happiness correlates with confidence
        )
        
        # Penalty for excessive fear/sad
        confidence -= (probs.get('fear', 0) + probs.get('sad', 0)) * 15
        
        return min(100, max(0, confidence))
    
    def _calculate_stability(self, results):
        """Calculate emotional stability (low variance = high stability)"""
        # For video: use frame emotions
        if 'visual' in results:
            frame_emotions = results.get('visual', {}).get('frame_emotions', [])
            
            if len(frame_emotions) < 2:
                return 75.0  # Default for short videos
            
            # Count emotion transitions
            transitions = 0
            for i in range(1, len(frame_emotions)):
                if frame_emotions[i] != frame_emotions[i-1]:
                    transitions += 1
            
            # Fewer transitions = more stable
            transition_rate = transitions / len(frame_emotions)
            stability = (1 - transition_rate) * 100
            
            return min(100, max(0, stability))
        else:
            # For audio-only: use audio vs text consistency
            if 'audio' in results and 'text' in results:
                audio_emotion = results['audio'].get('dominant_emotion', 'neutral')
                text_emotion = results['text'].get('dominant_emotion', 'neutral')
                
                # If audio and text agree, high stability
                if audio_emotion == text_emotion:
                    return 85.0
                else:
                    return 60.0
            
            return 75.0  # Default
    
    def _calculate_positivity(self, probs):
        """Calculate overall positivity"""
        positive = probs.get('happy', 0) * 2.0
        negative = (
            probs.get('angry', 0) +
            probs.get('sad', 0) +
            probs.get('fear', 0) +
            probs.get('disgust', 0)
        )
        
        positivity = (positive - negative + 1) / 2 * 100
        return min(100, max(0, positivity))
    
    def _calculate_communication(self, results):
        """Calculate communication quality based on transcript"""
        transcript = results.get('transcript', {}).get('text', '')
        
        if not transcript or transcript == "No speech detected":
            return 0.0
        
        words = transcript.split()
        word_count = len(words)
        
        if word_count == 0:
            return 0.0
        
        # Factors for good communication
        score = 50  # Base score
        
        # 1. Word count (ideal range: 50-200 words per minute)
        duration = results.get('duration', 1)
        wpm = word_count / (duration / 60)
        if 50 <= wpm <= 200:
            score += 20
        elif wpm < 50:
            score += 10
        
        # 2. Vocabulary diversity
        unique_words = len(set(w.lower() for w in words))
        diversity = unique_words / word_count
        score += diversity * 20
        
        # 3. Sentence structure (penalize very short sentences)
        sentences = transcript.count('.') + transcript.count('?') + transcript.count('!')
        if sentences > 0:
            avg_words_per_sentence = word_count / sentences
            if 8 <= avg_words_per_sentence <= 20:
                score += 10
        
        return min(100, max(0, score))
    
    def _calculate_overall(self, metrics):
        """Calculate overall performance score"""
        weights = {
            'engagement': 0.25,
            'confidence': 0.25,
            'communication': 0.20,
            'positivity': 0.15,
            'stability': 0.10
        }
        
        # Stress is negative (lower is better)
        overall = sum(metrics.get(key, 0) * weight 
                     for key, weight in weights.items())
        
        # Subtract stress impact
        overall -= metrics.get('stress', 0) * 0.05
        
        return min(100, max(0, overall))
    
    def _generate_recommendations(self, metrics):
        """
        Generate precise, evidence-based recommendations
        tightly coupled to how metrics are calculated
        """

        recs = []

        def add(category, issue, evidence, suggestion, priority):
            recs.append({
                "category": category,
                "issue": issue,
                "evidence": evidence,
                "suggestion": suggestion,
                "priority": priority
            })

        # ---------------- STRESS ----------------
        stress = metrics.get("stress", 0)
        if stress >= 80:
            add(
                "Stress Management",
                "Critical stress indicators",
                f"Stress score {stress:.1f}/100 driven by fear/sad emotions and filler words.",
                "Reduce cognitive load: rehearse 3 key stories, pause 1–2 seconds before answering, and slow speech by ~10%.",
                priority=1
            )
        elif stress >= 60:
            add(
                "Stress Management",
                "Elevated stress",
                f"Stress score {stress:.1f}/100 suggests nervous speech patterns.",
                "Practice mock interviews under time pressure and consciously remove filler words (um, uh, like).",
                priority=2
            )

        # ---------------- ENGAGEMENT ----------------
        engagement = metrics.get("engagement", 100)
        if engagement < 30:
            add(
                "Engagement",
                "Very low engagement",
                f"Engagement score {engagement:.1f}/100 indicates limited facial and vocal variation.",
                "Increase expressiveness: emphasize key words, vary pitch, and show reactions when describing outcomes.",
                priority=1
            )
        elif engagement < 50:
            add(
                "Engagement",
                "Below-average engagement",
                f"Engagement score {engagement:.1f}/100 with neutral-dominant expressions.",
                "Add intentional emphasis at the start and end of responses to signal interest.",
                priority=3
            )

        # ---------------- CONFIDENCE ----------------
        confidence = metrics.get("confidence", 100)
        if confidence < 30:
            add(
                "Confidence",
                "Very low confidence signals",
                f"Confidence score {confidence:.1f}/100 indicates high hesitation and emotional uncertainty.",
                "Use structured answers (STAR) and finish statements decisively without rising intonation.",
                priority=1
            )
        elif confidence < 50:
            add(
                "Confidence",
                "Moderate confidence issues",
                f"Confidence score {confidence:.1f}/100 shows emotional inconsistency.",
                "Reduce fillers and replace with short pauses to sound more deliberate.",
                priority=3
            )

        # ---------------- COMMUNICATION ----------------
        communication = metrics.get("communication", 100)
        if communication < 40:
            add(
                "Communication",
                "Poor response clarity",
                f"Communication score {communication:.1f}/100 suggests weak structure or pacing.",
                "Limit answers to 60–90 seconds and explicitly label Situation, Action, Result.",
                priority=2
            )
        elif communication < 60:
            add(
                "Communication",
                "Inconsistent communication quality",
                f"Communication score {communication:.1f}/100 indicates pacing or sentence issues.",
                "Pause between points and aim for 8–15 words per sentence.",
                priority=4
            )

        # ---------------- STABILITY ----------------
        stability = metrics.get("stability", 100)
        if stability < 40:
            add(
                "Emotional Control",
                "High emotional fluctuation",
                f"Stability score {stability:.1f}/100 shows frequent emotion shifts.",
                "Maintain neutral facial baseline during technical or difficult questions.",
                priority=2
            )
        elif stability < 50:
            add(
                "Emotional Control",
                "Moderate emotional inconsistency",
                f"Stability score {stability:.1f}/100 suggests occasional emotional drift.",
                "Focus on steady tone and controlled breathing during longer answers.",
                priority=4
            )

        # ---------------- POSITIVITY ----------------
        positivity = metrics.get("positivity", 100)
        if positivity < 40:
            add(
                "Positivity",
                "Low positive affect",
                f"Positivity score {positivity:.1f}/100 driven by negative emotional weight.",
                "Reframe answers to emphasize outcomes, learning, and growth.",
                priority=3
            )
        elif positivity < 50:
            add(
                "Positivity",
                "Limited positive expression",
                f"Positivity score {positivity:.1f}/100 with neutral-heavy tone.",
                "End responses with a positive takeaway or impact statement.",
                priority=5
            )

        # ---------------- OVERALL ----------------
        overall = metrics.get("overall", 0)
        if overall >= 80:
            add(
                "Overall",
                "Strong interview performance",
                f"Overall score {overall:.1f}/100 indicates high readiness.",
                "Focus only on polishing weakest metrics rather than broad changes.",
                priority=6
            )

        # Sort by importance (lower = more critical)
        recs.sort(key=lambda r: r["priority"])

        return recs


    def get_metric_color(self, score):
        """Get color based on score"""
        if score >= 75:
            return '#2ECC71'  # Green
        elif score >= 50:
            return '#F39C12'  # Orange
        else:
            return '#E74C3C'  # Red
    
    def get_metric_label(self, score):
        """Get label based on score"""
        if score >= 75:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Fair'
        else:
            return 'Needs Improvement'
