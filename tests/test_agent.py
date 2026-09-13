from unittest.mock import patch

from app.agent import classify_node, route_after_cache


def test_classify_node_sets_escalate_true_for_critical():
    with patch("app.agent.classifier_tokenizer") as mock_tokenizer, \
         patch("app.agent.classifier_model") as mock_model:

        import torch
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        # CRITICAL is index 2 in LABELS = ["MEDIUM", "HIGH", "CRITICAL"]
        mock_model.return_value.logits = torch.tensor([[0.1, 0.1, 0.9]])

        state = {"description": "some fake CVE description"}
        result = classify_node(state)

        assert result["severity"] == "CRITICAL"
        assert result["escalate"] is True


def test_classify_node_does_not_escalate_for_high():
    with patch("app.agent.classifier_tokenizer") as mock_tokenizer, \
         patch("app.agent.classifier_model") as mock_model:

        import torch
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        # HIGH is index 1
        mock_model.return_value.logits = torch.tensor([[0.1, 0.9, 0.1]])

        state = {"description": "some fake CVE description"}
        result = classify_node(state)

        assert result["severity"] == "HIGH"
        assert result["escalate"] is False


def test_route_after_cache_hit_goes_to_end():
    from langgraph.graph import END
    state = {"_cache_hit": True}
    assert route_after_cache(state) == END


def test_route_after_cache_miss_goes_to_retrieve():
    state = {"_cache_hit": False}
    assert route_after_cache(state) == "retrieve"