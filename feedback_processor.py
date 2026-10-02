from textblob import TextBlob

class FeedbackProcessor:
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of the feedback text.
        Returns tuple of (sentiment_label, sentiment_score)
        """
        analysis = TextBlob(text)
        score = analysis.sentiment.polarity
        
        if score > 0:
            return "positive", score
        elif score < 0:
            return "negative", score
        return "neutral", score