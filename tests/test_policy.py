from doosan_python.models.policy import MockPolicy


def test_mock_policy_alternates_joint_delta():
    policy = MockPolicy(joint_index=6, delta_deg=10.0)
    joints = [0.0] * 6

    assert policy.predict(joints) == [0.0, 0.0, 0.0, 0.0, 0.0, 10.0]
    assert policy.predict(joints) == [0.0, 0.0, 0.0, 0.0, 0.0, -10.0]


def test_mock_policy_rejects_invalid_observation():
    policy = MockPolicy(joint_index=6, delta_deg=10.0)

    try:
        policy.predict([0.0] * 5)
    except ValueError as error:
        assert "6 joint" in str(error)
    else:
        raise AssertionError("invalid observation was accepted")
