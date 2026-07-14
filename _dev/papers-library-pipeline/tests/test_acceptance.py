from papers_library_pipeline.candidates import assign_local_ids, is_accepted


def test_is_accepted_true_for_accepted_or_selected():
    assert is_accepted({"accepted": True})
    assert is_accepted({"accepted": "yes"})
    assert is_accepted({"selected": True})
    assert is_accepted({"selected": "yes"})
    assert is_accepted({"accepted": "是"})
    assert not is_accepted({"accepted": False, "selected": False})
    assert not is_accepted({})
    assert not is_accepted({"accepted": "no"})


def test_assign_local_ids_only_selected_honors_accepted():
    items = [
        {"title": "A", "accepted": True},
        {"title": "B", "selected": True},
        {"title": "C", "accepted": False},
    ]
    out, nid = assign_local_ids(items, 1000, only_selected=True)
    assert out[0]["local_id"] == 1000
    assert out[1]["local_id"] == 1001
    assert "local_id" not in out[2]
    assert nid == 1002
