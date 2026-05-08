DEFAULT_TEMPLATES = {
    "podcast_default": {
        "name": "Podcast Standard", "category": "podcast",
        "description": "Default podcast editing template with speaker switching and silence trimming",
        "config": {
            "grade": "neutral_punch",
            "caption_style": {"font": "Helvetica", "size": 18, "bold": True, "case": "upper", "chunk_size": 2, "margin_v": 90, "color": "#FFFFFF", "outline": "#000000"},
            "cuts": {"silence_threshold_ms": 400, "filler_removal": True, "speaker_gap_ms": 500},
            "reframe": {"aspect": "16:9", "mode": "crop"},
            "exports": [{"preset": "youtube", "label": "Full Episode"}, {"preset": "tiktok", "label": "Short Clip"}],
        },
    },
    "rap_video_default": {
        "name": "Rap Video Standard", "category": "rap",
        "description": "High-energy rap video edits with beat-synced cuts and kinetic captions",
        "config": {
            "grade": "warm_cinematic",
            "caption_style": {"font": "Helvetica", "size": 20, "bold": True, "case": "upper", "chunk_size": 1, "margin_v": 80, "color": "#FF5A00", "outline": "#000000"},
            "cuts": {"silence_threshold_ms": 200, "filler_removal": False, "beat_sync": True},
            "reframe": {"aspect": "9:16", "mode": "crop"},
            "exports": [{"preset": "tiktok", "label": "Vertical"}, {"preset": "youtube", "label": "Full Video"}],
        },
    },
    "interview_default": {
        "name": "Interview Standard", "category": "interview",
        "description": "Interview editing with speaker labels, Q&A structure, and clean cuts",
        "config": {
            "grade": "neutral_punch",
            "caption_style": {"font": "Helvetica", "size": 16, "bold": False, "case": "sentence", "chunk_size": 4, "margin_v": 70, "color": "#FFFFFF", "outline": "#000000"},
            "cuts": {"silence_threshold_ms": 500, "filler_removal": True, "speaker_gap_ms": 600},
            "reframe": {"aspect": "16:9", "mode": "crop"},
            "exports": [{"preset": "youtube", "label": "Full Interview"}, {"preset": "tiktok", "label": "Highlight Clip"}],
        },
    },
}


def get_default_templates() -> dict:
    return DEFAULT_TEMPLATES
