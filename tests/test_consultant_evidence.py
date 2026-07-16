import pytest

from app.consultant.evidence import schema_fingerprint, validate_schema_payload


def test_schema_snapshot_only_accepts_metadata_shape():
    payload = validate_schema_payload({"tables": [{"name": "B30AccDoc", "fields": ["RowID", "DocDate"],
                                                   "relations": [{"to": "B00"}]}]})
    assert payload["tables"][0]["name"] == "B30AccDoc"
    assert schema_fingerprint(payload) == schema_fingerprint(payload)


@pytest.mark.parametrize("payload", [{}, {"tables": []}, {"tables": [{"name": "T", "fields": [1]}]}])
def test_schema_snapshot_rejects_non_metadata_shape(payload):
    with pytest.raises(ValueError):
        validate_schema_payload(payload)
