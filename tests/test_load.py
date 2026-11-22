from agentipc.load import experiments, load_records, load_rows


def test_committed_rows_load():
    assert "t07_main" in experiments()
    df = load_rows("t07_main")
    assert {"task_id", "channel", "dataset", "k", "acc", "total_tokens", "prefill_tokens"} <= set(df.columns)
    assert len(df) == 5400 and df["error"].eq("").all()
    assert round(df[(df.k == 3) & (df.channel == "A1")].acc.mean() * 100, 1) == 72.3


def test_committed_records_load():
    rec = next(load_records("t09_scope"))
    assert {"task_id", "channel", "agents", "io_ops", "stage", "score"} <= set(rec)
