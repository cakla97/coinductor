from coinductor.local_ai_recommender import LocalAiRecommender


def test_local_ai_recommender_prefers_14b_for_strong_gpu() -> None:
    recommendations = LocalAiRecommender()._recommend(ram_gb=31, gpu_vram_gb=16)

    assert recommendations[0].model == "qwen3:14b"
    assert recommendations[0].fit == "Best fit"


def test_local_ai_recommender_prefers_smaller_models_without_gpu() -> None:
    recommendations = LocalAiRecommender()._recommend(ram_gb=8, gpu_vram_gb=0)

    assert recommendations[0].model == "llama3.2:3b"
    assert any(item.model == "qwen3:1.7b" for item in recommendations)


def test_local_ai_recommender_snapshot_has_summary_and_recommendations() -> None:
    snapshot = LocalAiRecommender().inspect()

    assert "RAM" in snapshot.summary
    assert snapshot.recommendations
