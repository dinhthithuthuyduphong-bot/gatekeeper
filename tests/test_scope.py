def test_instance_in_predicate():
    from gatekeeper.scope import TargetContext, evaluate_predicate

    pred = {"kind": "instance_in", "ids": ["a__b-1", "c__d-2"]}
    assert evaluate_predicate(pred, TargetContext(name="b", fingerprints={}, task_id="a__b-1"))
    assert not evaluate_predicate(pred, TargetContext(name="b", fingerprints={}, task_id="x__y-3"))
