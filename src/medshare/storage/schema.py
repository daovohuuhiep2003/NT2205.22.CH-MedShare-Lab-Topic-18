"""
Database schema and collection specifications for MedShare-Lab encrypted storage (Zone Z2).
Applies to MongoDB 7.0 document collections.
"""

# MongoDB Collection Names
COLLECTION_CAPSULES = "key_capsules"
COLLECTION_PATIENTS = "encrypted_patients"
COLLECTION_SEARCH_INDEX = "search_index"

# Index specifications for MongoDB collections
MONGO_INDEX_SPECS = {
    COLLECTION_CAPSULES: [
        {"keys": [("capsule_id", 1)], "unique": True},
        {"keys": [("tenant_id", 1)]},
    ],
    COLLECTION_PATIENTS: [
        {"keys": [("record_id", 1)], "unique": True},
        {"keys": [("tenant_id", 1), ("patient_id_bidx", 1)]},
    ],
    COLLECTION_SEARCH_INDEX: [
        {
            "keys": [
                ("tenant_id", 1),
                ("field_name", 1),
                ("search_epoch", 1),
                ("token", 1),
            ]
        },
        {"keys": [("record_id", 1)]},
    ],
}
