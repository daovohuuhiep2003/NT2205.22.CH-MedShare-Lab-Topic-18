"""
MedShare-Lab: Cryptographic Exception Definitions (Topic 18 — NT2205.11.CH).
Phân cấp ngoại lệ bảo mật: Fail-closed và không lộ chi tiết nhạy cảm.
"""


class CryptoError(Exception):
    """Lớp cha cho toàn bộ lỗi trong hệ thống mật mã MedShare-Lab."""
    pass


class InvalidKeyError(CryptoError):
    """Ngoại lệ khi khóa DEK hoặc KEK không đúng định dạng hoặc độ dài."""
    pass


class EnvelopeValidationError(CryptoError):
    """Ngoại lệ khi Envelope bị định dạng sai, không thuộc allowlist hoặc vượt kích thước."""
    pass


class ContextMismatchError(CryptoError):
    """
    Ngoại lệ phát hiện tấn công tráo ngữ cảnh (Context Swapping / Splicing Attack).
    Xảy ra khi context trong bản mã không khớp với expected context từ TCB/Registry.
    """
    pass


class DecryptionIntegrityError(CryptoError):
    """
    Ngoại lệ khi kiểm tra tính toàn vẹn thất bại: Ciphertext, Tag hoặc AAD bị sửa đổi bit.
    """
    pass


class GcmAuthTagMismatchError(DecryptionIntegrityError):
    """Ngoại lệ khi AES-GCM Authentication Tag không khớp."""
    pass


class RecordTamperedError(DecryptionIntegrityError):
    """Ngoại lệ khi phát hiện dữ liệu bản ghi/file bị giả mạo hoặc tráo đổi."""
    pass


class TenantIsolationViolationError(CryptoError):
    """
    Ngoại lệ vi phạm ranh giới cô lập đa tenant (TC-06 Cross-tenant access violation).
    """
    pass


class EnvelopeBoundsExceededError(EnvelopeValidationError):
    """Vượt quá kích thước tối đa cho phép của Envelope / Capsule."""
    pass


class InvalidEnvelopeError(EnvelopeValidationError):
    """Định dạng Envelope / Capsule không hợp lệ."""
    pass


class AccessDeniedError(CryptoError):
    """Ngoại lệ khi yêu cầu bị từ chối bởi chính sách ABAC hoặc Broker PEP."""
    pass


class UnsupportedQueryError(CryptoError):
    """
    Ngoại lệ khi truy vấn không được hỗ trợ bởi Equality Blind Index.
    Từ chối các truy vấn range, pattern, regex, wildcard (HTTP 422 Unprocessable Entity).
    """

    def __init__(self, message: str = "Unsupported query type for Equality Blind Index", status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code



