#!/usr/bin/env python3
"""
Professional Multi-Page Draw.io Generator for MedShare-Lab (Topic 18).
Generates an elegant, pixel-perfect, enterprise-grade architecture & workflow diagram.
"""

import html
import os
import xml.etree.ElementTree as ET

def build_card_html(title, desc_items, header_color="#0284C7", title_color="#FFFFFF", badge=""):
    """Creates a modern enterprise card layout with styled header and body."""
    badge_html = f"<span style='float:right;background:rgba(255,255,255,0.25);padding:1px 6px;border-radius:3px;font-size:9px;'>{badge}</span>" if badge else ""
    items_html = "".join([f"<li style='margin-bottom:3px;'>{item}</li>" for item in desc_items])
    
    content = (
        f"<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;width:100%;height:100%;box-sizing:border-box;'>"
        f"<div style='background-color:{header_color};color:{title_color};padding:6px 10px;font-weight:700;font-size:11.5px;border-radius:5px 5px 0 0;letter-spacing:0.3px;'>"
        f"{title} {badge_html}"
        f"</div>"
        f"<div style='padding:8px 10px;font-size:10.5px;color:#1E293B;line-height:1.45;background-color:#FFFFFF;border-radius:0 0 5px 5px;'>"
        f"<ul style='margin:0;padding-left:14px;list-style-type:square;'>"
        f"{items_html}"
        f"</ul>"
        f"</div>"
        f"</div>"
    )
    return content

def build_step_html(step_num, title, actor, desc, step_color="#16A34A"):
    """Creates a numbered workflow step card."""
    content = (
        f"<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;width:100%;height:100%;box-sizing:border-box;'>"
        f"<div style='background-color:{step_color};color:#FFFFFF;padding:5px 8px;font-weight:700;font-size:11px;border-radius:5px 5px 0 0;display:flex;justify-content:space-between;'>"
        f"<span>BƯỚC {step_num}: {title}</span>"
        f"<span style='background:rgba(0,0,0,0.18);padding:1px 5px;border-radius:3px;font-size:9px;'>{actor}</span>"
        f"</div>"
        f"<div style='padding:7px 9px;font-size:10px;color:#334155;line-height:1.4;background-color:#FFFFFF;border-radius:0 0 5px 5px;'>"
        f"{desc}"
        f"</div>"
        f"</div>"
    )
    return content

class DiagramBuilder:
    def __init__(self, page_id, page_name, width=1920, height=1200):
        self.page_id = page_id
        self.page_name = page_name
        self.width = width
        self.height = height
        self.diagram_elem = ET.Element('diagram', {'id': page_id, 'name': page_name})
        self.model_elem = ET.SubElement(self.diagram_elem, 'mxGraphModel', {
            'dx': '1600',
            'dy': '1000',
            'grid': '1',
            'gridSize': '10',
            'guides': '1',
            'tooltips': '1',
            'connect': '1',
            'arrows': '1',
            'fold': '1',
            'page': '1',
            'pageScale': '1',
            'pageWidth': str(width),
            'pageHeight': str(height),
            'background': '#F8FAFC',
            'math': '0',
            'shadow': '0'
        })
        self.root = ET.SubElement(self.model_elem, 'root')
        ET.SubElement(self.root, 'mxCell', {'id': '0'})
        ET.SubElement(self.root, 'mxCell', {'id': '1', 'parent': '0'})
        self.counter = 100

    def add_cell(self, cell_id, value, style, x, y, width, height, parent='1', is_vertex=True):
        cid = str(cell_id) if cell_id is not None else str(self.counter)
        self.counter += 1
        attrs = {'id': cid, 'value': value, 'style': style, 'parent': parent}
        if is_vertex:
            attrs['vertex'] = '1'
        cell = ET.SubElement(self.root, 'mxCell', attrs)
        ET.SubElement(cell, 'mxGeometry', {
            'x': str(x), 'y': str(y), 'width': str(width), 'height': str(height), 'as': 'geometry'
        })
        return cid

    def add_edge(self, edge_id, value, style, source, target, waypoints=None, parent='1'):
        eid = str(edge_id) if edge_id is not None else str(self.counter)
        self.counter += 1
        attrs = {
            'id': eid, 'value': value, 'style': style, 'parent': parent,
            'edge': '1', 'source': source, 'target': target
        }
        cell = ET.SubElement(self.root, 'mxCell', attrs)
        geo = ET.SubElement(cell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})
        if waypoints:
            array = ET.SubElement(geo, 'Array', {'as': 'points'})
            for wx, wy in waypoints:
                ET.SubElement(array, 'mxPoint', {'x': str(wx), 'y': str(wy)})
        return eid


def create_all_pages():
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2026-10-07T00:45:00.000Z',
        'agent': 'MedShare Enterprise Architecture Modeler',
        'version': '21.0.0',
        'type': 'device'
    })

    # =========================================================================
    # TAB 1: TỔNG QUAN KIẾN TRÚC & PHÂN VÙNG TIN CẬY (SYSTEM ARCHITECTURE)
    # =========================================================================
    p1 = DiagramBuilder('page_arch', '1. Kiến trúc Tổng thể & 4 Vùng Tin cậy', 1860, 1150)
    
    # 1. Header Banner
    header_html = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;text-align:center;color:#0F172A;'>"
        "<div style='font-size:21px;font-weight:800;letter-spacing:0.5px;color:#1E293B;'>"
        "HỆ THỐNG BẢO VỆ DỮ LIỆU Y TẾ ĐA TENANT TRÊN CLOUD DBMS (MEDSHARE-LAB - TOPIC 18)</div>"
        "<div style='margin-top:4px;font-size:12.5px;color:#475569;'>"
        "Mô hình kiến trúc 4 vùng tin cậy (Z0-Z3) | Envelope Encryption (AES-256-GCM) | ABAC | Blind Index | Vault KMS | CP-ABE | SEAL BFV"
        "</div></div>"
    )
    p1.add_cell('banner1', header_html,
                'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=1.5;shadow=0;arcSize=6;',
                40, 20, 1780, 65)

    # 2. Zone Containers (Z0, Z1, Z2, Z3)
    # Zone Z0
    z0_style = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=14;spacingTop=10;fontStyle=1;fontSize=13;fontColor=#0369A1;'
    p1.add_cell('zone_z0', '<b>VÙNG Z0: NGƯỜI DÙNG &amp; THIẾT BỊ ĐẦU CUỐI (CLIENT ZONE)</b>', z0_style, 40, 105, 310, 690)

    # Zone Z1
    z1_style = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;strokeWidth=2;dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=14;spacingTop=10;fontStyle=1;fontSize=13;fontColor=#15803D;'
    p1.add_cell('zone_z1', '<b>VÙNG Z1: MIỀN TỔ CHỨC TIN CẬY (TRUSTED GATEWAY &amp; KEY MANAGEMENT)</b>', z1_style, 380, 105, 750, 690)

    # Zone Z2
    z2_style = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=2;dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=14;spacingTop=10;fontStyle=1;fontSize=13;fontColor=#B91C1C;'
    p1.add_cell('zone_z2', '<b>VÙNG Z2: ĐÁM MÂY KHÔNG TIN CẬY (UNTRUSTED CLOUD DBMS &amp; WORKERS)</b>', z2_style, 1160, 105, 660, 690)

    # Zone Z3
    z3_style = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#475569;strokeWidth=2;dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=14;spacingTop=8;fontStyle=1;fontSize=13;fontColor=#334155;'
    p1.add_cell('zone_z3', '<b>VÙNG Z3: KIỂM TOÁN &amp; GIÁM SÁT ĐỘC LẬP (INDEPENDENT AUDIT &amp; GOVERNANCE)</b>', z3_style, 40, 815, 1780, 145)

    # 3. Nodes inside Z0
    card_base = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=1;arcSize=6;shadow=1;'
    
    c_user = build_card_html("Bác sĩ / Nhà nghiên cứu", [
        "Người dùng nghiệp vụ (Doctor/Nurse)",
        "Gửi truy vấn đọc/ghi hồ sơ bệnh án",
        "Xác thực qua mTLS / OpenID Connect"
    ], header_color="#0284C7", badge="ACTOR")
    p1.add_cell('node_user', c_user, card_base, 65, 150, 260, 110)

    c_portal = build_card_html("MedShare Portal / EMR App", [
        "Ứng dụng bệnh viện / Web Client",
        "Giao tiếp qua kênh an toàn TLS 1.3 (F1)",
        "Gửi kèm JWT Bearer Token theo phiên"
    ], header_color="#0284C7", badge="Z0 APP")
    p1.add_cell('node_portal', c_portal, card_base, 65, 290, 260, 110)

    c_sdk = build_card_html("Recipient SDK (CP-ABE)", [
        "Engine giải mã chia sẻ liên viện",
        "Lưu giữ User Secret Keys theo thuộc tính",
        "Giải mã ngoại tuyến độc lập (Offline)"
    ], header_color="#7C3AED", badge="PROFILE P2")
    p1.add_cell('node_sdk', c_sdk, card_base, 65, 450, 260, 115)

    c_viewer = build_card_html("Safe Clinical Viewer", [
        "Trình hiển thị dữ liệu an toàn",
        "Chỉ render trường được PDP cấp phép",
        "Không lưu vết cache plaintext nhạy cảm"
    ], header_color="#0284C7", badge="VIEWER")
    p1.add_cell('node_viewer', c_viewer, card_base, 65, 615, 260, 110)

    # 4. Nodes inside Z1 (2 Columns: Pipeline Tier & Authority Tier)
    # Column 1 (Left in Z1 - Core Execution): x = 405, w = 340
    c_gateway = build_card_html("Trusted Crypto Gateway", [
        "Điểm tiếp nhận tập trung (API Entry Point)",
        "Thực thi điểm chốt chính sách PEP",
        "Phân rã request &amp; điều phối mã hóa"
    ], header_color="#16A34A", badge="PEP / API")
    p1.add_cell('node_gateway', c_gateway, card_base, 405, 150, 340, 110)

    c_engine = build_card_html("FieldCipherEngine &amp; Blind Index", [
        "Mã hóa AES-256-GCM (12-byte CSPRNG Nonce)",
        "Ràng buộc AAD RFC 8785 (JCS Canonical)",
        "Blind Index: HMAC-SHA256 Token (F4)"
    ], header_color="#16A34A", badge="M-01/M-02")
    p1.add_cell('node_engine', c_engine, card_base, 405, 290, 340, 120)

    c_broker = build_card_html("Key Broker &amp; Independent PEP", [
        "Quản lý vòng đời DEK phân cấp Tenant/Class",
        "Đối soát quyền truy cập khóa với PDP độc lập",
        "Ủy quyền bọc/gỡ DEK sang KMS (F0/F8)"
    ], header_color="#CA8A04", badge="PEP KEY")
    p1.add_cell('node_broker', c_broker, card_base, 405, 440, 340, 115)

    c_kms = build_card_html("Software KMS (HashiCorp Vault)", [
        "Transit Secret Engine (Port 8200)",
        "Bảo vệ Master KEK &amp; Tenant KEK",
        "Wrap/Unwrap DEK &rarr; KeyCapsule an toàn"
    ], header_color="#CA8A04", badge="Z1 KMS")
    p1.add_cell('node_kms', c_kms, card_base, 405, 585, 340, 115)

    # Column 2 (Right in Z1 - Control & Authority): x = 765, w = 340
    c_idp = build_card_html("Identity Provider (IdP) &amp; PIP", [
        "Xác thực danh tính người dùng (OAuth2/JWT)",
        "Cung cấp Policy Information Point (PIP)",
        "Truy xuất thuộc tính: Vai trò, Khoa, Tenant"
    ], header_color="#15803D", badge="IdP / PIP")
    p1.add_cell('node_idp', c_idp, card_base, 765, 150, 340, 110)

    c_pdp = build_card_html("ABAC PDP (Policy Decision Point)", [
        "Động cơ phân quyền Deny-by-Default",
        "Đánh giá Subject, Object, Action, Context",
        "Trả quyết định: Permit / Deny + Policy Ver"
    ], header_color="#15803D", badge="PDP CORE")
    p1.add_cell('node_pdp', c_pdp, card_base, 765, 290, 340, 115)

    c_reg = build_card_html("Trusted Manifest Registry", [
        "Quản lý Schema &amp; Manifest các trường",
        "Theo dõi phiên bản KEK/DEK đang hoạt động",
        "Freshness Check chống tấn công Replay (F8)"
    ], header_color="#15803D", badge="REGISTRY")
    p1.add_cell('node_reg', c_reg, card_base, 765, 435, 340, 115)

    c_aa = build_card_html("Attribute Authority (CP-ABE)", [
        "Nắm giữ Master Secret Key thuật toán AC17",
        "Cấp phát User Secret Key theo thuộc tính",
        "Phát hành Public Parameters cho bên chia sẻ"
    ], header_color="#7C3AED", badge="AUTH AA")
    p1.add_cell('node_aa', c_aa, card_base, 765, 580, 340, 120)

    # 5. Nodes inside Z2 (2 Columns: DBMS Storage & Workers)
    # Column 1 (Left in Z2 - Storage Tier): x = 1185, w = 300
    c_db = build_card_html("Untrusted Cloud DBMS", [
        "PostgreSQL 16 (5432) &amp; MongoDB 7.0 (27017)",
        "Lưu <b>FieldEnvelope</b> (Ciphertext + Tag)",
        "Lưu <b>KeyCapsule</b> (Wrapped DEK bởi KEK)",
        "Lưu <b>Blind Index</b> (HMAC Token tra cứu)"
    ], header_color="#DC2626", badge="SQL/NOSQL")
    p1.add_cell('node_db', c_db, card_base, 1185, 150, 300, 140)

    c_replica = build_card_html("Cloud Replicas &amp; Backups", [
        "Replication Streams (WAL / Oplog CDC)",
        "Volume Snapshot đĩa cứng (LUKS Entropy 7.99)",
        "Không rò rỉ Plaintext khi snapshot bị đánh cắp"
    ], header_color="#DC2626", badge="BACKUP")
    p1.add_cell('node_replica', c_replica, card_base, 1185, 320, 300, 115)

    c_he_worker = build_card_html("HE Worker (SEAL BFV)", [
        "Docker Container: Microsoft SEAL v4.1.2 C++",
        "Tính toán Encrypted Sum trên bản mã",
        "Không biết nội dung và không cần giải mã"
    ], header_color="#7C3AED", badge="PROFILE P3")
    p1.add_cell('node_he_worker', c_he_worker, card_base, 1185, 475, 300, 115)

    c_threat = build_card_html("Threat: Rogue DBA / Cloud Admin", [
        "Truy vấn trực tiếp DB: Chỉ thấy Base64 (TC-02)",
        "Sửa bit / tráo AAD: Bị chặn bởi GCM Tag (TC-05)",
        "Không thể giải mã vì không có KEK/DEK trong Z2"
    ], header_color="#991B1B", badge="ADVERSARY")
    p1.add_cell('node_threat', c_threat, card_base, 1185, 615, 300, 120)

    # Column 2 (Right in Z2 - Micro-workers): x = 1505, w = 295
    c_abe_worker = build_card_html("CP-ABE Worker (AC17)", [
        "Stanford PBC 0.5.14 + Charm-Crypto",
        "Mã hóa DEK theo Policy cây thuộc tính",
        "Hỗ trợ chia sẻ hồ sơ liên viện an toàn"
    ], header_color="#7C3AED", badge="AC17 WORKER")
    p1.add_cell('node_abe_worker', c_abe_worker, card_base, 1505, 150, 295, 115)

    c_pqc_worker = build_card_html("PQC Worker (liboqs)", [
        "FIPS 203 ML-KEM-768 (KEM đóng gói)",
        "FIPS 204 ML-DSA-65 (Chữ ký điện tử)",
        "Bảo vệ dài hạn chống mối đe dọa Lượng tử"
    ], header_color="#475569", badge="PROFILE P4")
    p1.add_cell('node_pqc_worker', c_pqc_worker, card_base, 1505, 295, 295, 115)

    c_pqc_arch = build_card_html("PQC Long-Term Archival", [
        "Kho lưu trữ hồ sơ bệnh án vĩnh viễn",
        "Chống tấn công Harvest-Now-Decrypt-Later",
        "Đóng gói an toàn kết hợp Hybrid KEM"
    ], header_color="#475569", badge="P4 ARCHIVE")
    p1.add_cell('node_pqc_arch', c_pqc_arch, card_base, 1505, 440, 295, 115)

    c_sec_note = build_card_html("Bảo đảm An toàn Z2", [
        "Không bao giờ truyền KEK xuống Z2",
        "DEK chỉ tồn tại trong RAM của Z1",
        "Nguyên tắc phòng thủ theo chiều sâu"
    ], header_color="#DC2626", badge="GUARANTEE")
    p1.add_cell('node_sec_note', c_sec_note, card_base, 1505, 590, 295, 110)

    # 6. Nodes inside Z3 (Audit Tier): 3 horizontal cards
    c_audit_log = build_card_html("Append-Only Audit Log", [
        "Cấu trúc Merkle Tree Hash-Chained bất biến",
        "Ghi F9: <code>[op_id, subject_hash, policy_ver, kek_id, digest]</code>",
        "Nghiêm cấm ghi Plaintext hoặc Key Material"
    ], header_color="#334155", badge="F9 AUDIT")
    p1.add_cell('node_audit_log', c_audit_log, card_base, 70, 850, 520, 95)

    c_witness = build_card_html("External Checkpoint Witness", [
        "Ký số định kỳ trên Merkle Root Hash của Audit Log",
        "Lưu trữ mốc bằng chứng độc lập ngoài Cloud",
        "Chống chối bỏ và chống tấn công cắt tỉa nhật ký"
    ], header_color="#334155", badge="NOTARY")
    p1.add_cell('node_witness', c_witness, card_base, 650, 850, 520, 95)

    c_siem = build_card_html("Security SIEM &amp; Tamper Monitor", [
        "Giám sát liên tục các sự kiện vi phạm toàn vẹn (TC-05)",
        "Cảnh báo hành vi quét hàng loạt của Rogue DBA (TC-02)",
        "Tự động kích hoạt phong tỏa khẩn cấp khi có sự cố"
    ], header_color="#334155", badge="SIEM ALERTS")
    p1.add_cell('node_siem', c_siem, card_base, 1230, 850, 560, 95)

    # 7. Connectors in Architecture Overview (Orthogonal & Clean)
    edge_blue = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0284C7;strokeWidth=2;fontColor=#0369A1;fontSize=10;fontStyle=1;'
    edge_green = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16A34A;strokeWidth=2;fontColor=#15803D;fontSize=10;fontStyle=1;'
    edge_amber = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#CA8A04;strokeWidth=2;fontColor=#854D0E;fontSize=10;fontStyle=1;'
    edge_red = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#DC2626;strokeWidth=2;fontColor=#991B1B;fontSize=10;fontStyle=1;'
    edge_purple = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7C3AED;strokeWidth=2;fontColor=#6D28D9;fontSize=10;fontStyle=1;'
    edge_gray = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#64748B;strokeWidth=1.5;dashed=1;fontColor=#475569;fontSize=9;'

    p1.add_edge('e1_user_portal', '', edge_blue, 'node_user', 'node_portal')
    p1.add_edge('e1_portal_gw', 'F1: TLS 1.3 Request', edge_blue, 'node_portal', 'node_gateway')
    p1.add_edge('e1_gw_pdp', 'F2: Context Check', edge_green, 'node_gateway', 'node_pdp')
    p1.add_edge('e1_gw_engine', 'Plaintext / Fields', edge_green, 'node_gateway', 'node_engine')
    p1.add_edge('e1_engine_broker', 'Yêu cầu DEK', edge_amber, 'node_engine', 'node_broker')
    p1.add_edge('e1_broker_kms', 'Wrap DEK &rarr; Capsule', edge_amber, 'node_broker', 'node_kms')
    p1.add_edge('e1_engine_db', 'F3/F4: Envelopes + Blind Index', edge_red, 'node_engine', 'node_db')
    p1.add_edge('e1_db_replica', 'F7: Replication', edge_red, 'node_db', 'node_replica')
    p1.add_edge('e1_aa_sdk', 'Cấp User Secret Key', edge_purple, 'node_aa', 'node_sdk')
    p1.add_edge('e1_gw_audit', 'F9 Metadata', edge_gray, 'node_gateway', 'node_audit_log')
    p1.add_edge('e1_audit_wit', '', edge_gray, 'node_audit_log', 'node_witness')
    p1.add_edge('e1_wit_siem', '', edge_gray, 'node_witness', 'node_siem')

    mxfile.append(p1.diagram_elem)


    # =========================================================================
    # TAB 2: LUỒNG GHI HỒ SƠ Y TẾ & MÃ HÓA TẦNG TRƯỜNG (WRITE PIPELINE)
    # =========================================================================
    p2 = DiagramBuilder('page_write', '2. Luồng Ghi Hồ sơ (Write Pipeline)', 1860, 1150)

    # Header
    h2 = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;text-align:center;color:#0F172A;'>"
        "<div style='font-size:21px;font-weight:800;letter-spacing:0.5px;color:#15803D;'>"
        "QUY TRÌNH GHI HỒ SƠ &amp; MÃ HÓA TẦNG TRƯỜNG (WRITE &amp; INGESTION PIPELINE)</div>"
        "<div style='margin-top:4px;font-size:12.5px;color:#475569;'>"
        "Quy trình xử lý 7 bước từ Client (Z0) qua Gateway/KMS (Z1) đến Cloud DBMS (Z2) | Ràng buộc AAD RFC 8785 | Fail-Closed"
        "</div></div>"
    )
    p2.add_cell('banner2', h2, card_base, 40, 20, 1780, 65)

    # Swimlanes for Write Flow (Z0 -> Z1 -> Z2 -> Z3)
    p2.add_cell('wlane_z0', '<b>VÙNG Z0: CLIENT ENDPOINT</b>', z0_style, 40, 105, 340, 980)
    p2.add_cell('wlane_z1', '<b>VÙNG Z1: TRUSTED GATEWAY &amp; KEY BROKER</b>', z1_style, 410, 105, 780, 980)
    p2.add_cell('wlane_z2', '<b>VÙNG Z2: UNTRUSTED CLOUD DBMS</b>', z2_style, 1220, 105, 350, 980)
    p2.add_cell('wlane_z3', '<b>VÙNG Z3: AUDIT</b>', z3_style, 1600, 105, 220, 980)

    # 7 Step Cards
    w_step1 = build_step_html(1, "Gửi Hồ sơ Bệnh án", "EMR CLIENT",
        "• Bác sĩ nhập hồ sơ bệnh án (Tên, CCCD, Chẩn đoán, Nhóm máu).<br/>"
        "• Gửi HTTP POST JSON qua kênh mã hóa <b>TLS 1.3</b> kèm JWT token xác thực (F1).",
        step_color="#0284C7")
    p2.add_cell('w1', w_step1, card_base, 65, 160, 290, 105)

    w_step2 = build_step_html(2, "Xác thực &amp; Kiểm tra ABAC", "GATEWAY &amp; PDP",
        "• Gateway trích xuất Subject: <code>doctor_id</code>, <code>role</code>, <code>tenant_id</code>.<br/>"
        "• Gửi yêu cầu sang <b>PDP</b>: Đánh giá chính sách ABAC (Deny-by-default).<br/>"
        "• Nếu không hợp lệ &rarr; Từ chối ngay (Fail-closed). Nếu hợp lệ &rarr; Cho phép ghi.",
        step_color="#16A34A")
    p2.add_cell('w2', w_step2, card_base, 440, 160, 340, 115)

    w_step3 = build_step_html(3, "Yêu cầu Cấp phát Khóa DEK", "KEY BROKER",
        "• Gateway yêu cầu DEK tương ứng với cặp <code>(tenant_id, data_class)</code>.<br/>"
        "• Key Broker kiểm tra quyền độc lập, sinh ngẫu nhiên DEK 256-bit (CSPRNG).<br/>"
        "• DEK chỉ tồn tại trong bộ nhớ RAM tạm thời của Z1.",
        step_color="#CA8A04")
    p2.add_cell('w3', w_step3, card_base, 810, 160, 350, 115)

    w_step4 = build_step_html(4, "Bọc Khóa (Key Wrapping)", "VAULT KMS",
        "• Key Broker gọi HashiCorp Vault Transit API qua cổng 8200.<br/>"
        "• Vault dùng Tenant KEK bọc DEK &rarr; tạo ra <code>KeyCapsule</code>.<br/>"
        "• <code>KeyCapsule</code> chứa: <code>kek_id</code>, <code>version</code>, <code>wrapped_dek_b64</code>.",
        step_color="#CA8A04")
    p2.add_cell('w4', w_step4, card_base, 810, 350, 350, 115)

    w_step5 = build_step_html(5, "Mã hóa Trường &amp; Tính Blind Index", "CRYPTO ENGINE",
        "• <b>FieldCipherEngine</b> mã hóa từng trường nhạy cảm bằng AES-256-GCM.<br/>"
        "• Tạo Nonce 12-byte CSPRNG duy nhất cho mỗi trường (chống nonce reuse).<br/>"
        "• Ràng buộc AAD theo chuẩn <b>RFC 8785 JCS</b>: <code>tenant_id, object_id, field</code>.<br/>"
        "• Sinh Blind Index Token (HMAC-SHA256) cho các trường tra cứu chính xác.",
        step_color="#16A34A")
    p2.add_cell('w5', w_step5, card_base, 440, 480, 720, 130)

    w_step6 = build_step_html(6, "Lưu trữ Bản mã xuống Cloud DB", "CLOUD DBMS",
        "• Gateway gửi bản ghi đã mã hóa xuống PostgreSQL 16 / MongoDB 7.0 (F3).<br/>"
        "• Dữ liệu lưu trữ gồm: <code>FieldEnvelope</code> (Ciphertext + Tag + Salt),<br/>"
        "  <code>KeyCapsule</code> (bọc bởi KEK), và <code>token_bidx_hmac</code>.<br/>"
        "• <b>Cloud DB KHÔNG CÓ Plaintext và KHÔNG CÓ KEK!</b>",
        step_color="#DC2626")
    p2.add_cell('w6', w_step6, card_base, 1245, 480, 300, 140)

    w_step7 = build_step_html(7, "Ghi Nhật ký Kiểm toán Bất biến", "Z3 AUDIT LOG",
        "• Gateway và Broker gửi Metadata F9 sang Audit Log.<br/>"
        "• Ghi lại: <code>op_id</code>, <code>subject_hash</code>, <code>kek_id</code>, <code>digest</code>.<br/>"
        "• Nối vào Merkle Hash Chain bất biến để phục vụ kiểm toán độc lập.",
        step_color="#334155")
    p2.add_cell('w7', w_step7, card_base, 1620, 480, 180, 140)

    # Connecting Edges
    p2.add_edge('we1', 'F1: Request TLS', edge_blue, 'w1', 'w2')
    p2.add_edge('we2', 'Quyền Ghi Hợp lệ', edge_green, 'w2', 'w3')
    p2.add_edge('we3', 'Wrap DEK', edge_amber, 'w3', 'w4')
    p2.add_edge('we4', 'DEK + KeyCapsule', edge_amber, 'w4', 'w5')
    p2.add_edge('we5', 'F3: Ghi Ciphertext Envelopes', edge_red, 'w5', 'w6')
    p2.add_edge('we6', 'F9: Metadata Only', edge_gray, 'w5', 'w7')

    # Security Summary Panel for Write
    sec_write_html = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;padding:12px;color:#1E293B;'>"
        "<div style='font-weight:bold;color:#15803D;font-size:12px;margin-bottom:6px;'>CAM KẾT AN TOÀN TRONG QUY TRÌNH GHI (SECURITY INVARIANTS)</div>"
        "<div style='font-size:11px;line-height:1.6;display:grid;grid-template-columns:1fr 1fr;gap:15px;'>"
        "<div>"
        "• <b>Tính độc lập DEK:</b> Mỗi trường/bản ghi sử dụng Nonce CSPRNG 12-byte duy nhất, ngăn chặn triệt để tấn công Replay và rò rỉ khóa.<br/>"
        "• <b>Ràng buộc ngữ cảnh AAD (RFC 8785):</b> Bất biến gắn liền với <code>tenant_id</code>, ngăn chặn hoàn toàn việc tráo đổi dữ liệu giữa các bệnh viện (TC-05)."
        "</div>"
        "<div>"
        "• <b>Cô lập khóa KEK:</b> KEK được lưu trữ an toàn trong HashiCorp Vault KMS, không bao giờ được xuất ra ngoài RAM của Z1.<br/>"
        "• <b>Toàn vẹn kiểm toán (Audit Integrity):</b> Không có bất kỳ dữ liệu Plaintext hay khóa bí mật nào bị rò rỉ vào hệ thống log (F9)."
        "</div></div></div>"
    )
    p2.add_cell('w_sec_box', sec_write_html, card_base, 440, 680, 1360, 120)

    mxfile.append(p2.diagram_elem)


    # =========================================================================
    # TAB 3: LUỒNG ĐỌC HỒ SƠ & TRA CỨU BẢO MẬT (READ & SEARCH PIPELINE)
    # =========================================================================
    p3 = DiagramBuilder('page_read', '3. Luồng Đọc & Tra cứu Bảo mật (Read Pipeline)', 1860, 1150)

    # Header
    h3 = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;text-align:center;color:#0F172A;'>"
        "<div style='font-size:21px;font-weight:800;letter-spacing:0.5px;color:#D97706;'>"
        "QUY TRÌNH ĐỌC HỒ SƠ &amp; TRA CỨU BẢO MẬT (READ &amp; BLIND INDEX PIPELINE)</div>"
        "<div style='margin-top:4px;font-size:12.5px;color:#475569;'>"
        "Tra cứu chính xác qua Blind Index HMAC | Gỡ khóa DEK qua Vault KMS | Bắt buộc đối soát AAD &amp; Auth Tag | Safe Projection"
        "</div></div>"
    )
    p3.add_cell('banner3', h3, card_base, 40, 20, 1780, 65)

    # Swimlanes
    p3.add_cell('rlane_z0', '<b>VÙNG Z0: CLIENT ENDPOINT</b>', z0_style, 40, 105, 340, 980)
    p3.add_cell('rlane_z1', '<b>VÙNG Z1: TRUSTED GATEWAY &amp; KEY BROKER</b>', z1_style, 410, 105, 780, 980)
    p3.add_cell('rlane_z2', '<b>VÙNG Z2: UNTRUSTED CLOUD DBMS</b>', z2_style, 1220, 105, 350, 980)
    p3.add_cell('rlane_z3', '<b>VÙNG Z3: AUDIT</b>', z3_style, 1600, 105, 220, 980)

    # Steps for Read Flow
    r_step1 = build_step_html(1, "Truy vấn Tìm kiếm", "DOCTOR",
        "• Bác sĩ gửi yêu cầu tìm hồ sơ theo CCCD hoặc Mã bệnh án.<br/>"
        "• Truy vấn gửi qua TLS 1.3 kèm JWT chứa vai trò và khoa viện.",
        step_color="#0284C7")
    p3.add_cell('r1', r_step1, card_base, 65, 160, 290, 105)

    r_step2 = build_step_html(2, "Kiểm tra PDP &amp; Tính Blind Index", "GATEWAY &amp; PDP",
        "• Gateway xác thực quyền đọc của Bác sĩ qua <b>PDP</b>.<br/>"
        "• Tính toán Blind Index Token: <code>token = HMAC-SHA256(CCCD, salt_tenant)</code>.<br/>"
        "• Token là giá trị không thể đảo ngược, dùng để tìm kiếm chính xác (F4).",
        step_color="#16A34A")
    p3.add_cell('r2', r_step2, card_base, 440, 160, 350, 115)

    r_step3 = build_step_html(3, "Truy vấn DB bằng Token", "CLOUD DBMS",
        "• DB nhận câu lệnh: <code>SELECT * WHERE bidx_cccd = token</code>.<br/>"
        "• Cloud DB tìm kiếm chính xác cực nhanh nhưng <b>hoàn toàn không biết giá trị CCCD</b>.<br/>"
        "• Trả về các trường dạng <code>FieldEnvelope</code> và <code>KeyCapsule</code>.",
        step_color="#DC2626")
    p3.add_cell('r3', r_step3, card_base, 1245, 160, 300, 125)

    r_step4 = build_step_html(4, "Xác thực Quyền Gỡ Khóa (Unwrap)", "KEY BROKER",
        "• Gateway gửi <code>KeyCapsule</code> và Ngữ cảnh dự kiến sang Key Broker.<br/>"
        "• Key Broker đối soát độc lập với PDP và kiểm tra phiên bản tại Trusted Registry.<br/>"
        "• Nếu đối soát thất bại &rarr; Từ chối giải mã ngay lập tức.",
        step_color="#CA8A04")
    p3.add_cell('r4', r_step4, card_base, 820, 340, 350, 115)

    r_step5 = build_step_html(5, "Gỡ Khóa DEK An toàn", "VAULT KMS",
        "• Key Broker gọi Vault KMS Unwrap qua kênh an toàn nội bộ Z1.<br/>"
        "• Vault dùng Tenant KEK giải mã capsule và trả DEK về cho Key Broker.<br/>"
        "• DEK được nạp vào RAM của FieldCipherEngine trong phiên giải mã.",
        step_color="#CA8A04")
    p3.add_cell('r5', r_step5, card_base, 820, 500, 350, 115)

    r_step6 = build_step_html(6, "Giải mã &amp; Xác thực Toàn vẹn", "CRYPTO ENGINE",
        "• FieldCipherEngine tính lại Canonical AAD (RFC 8785) từ metadata.<br/>"
        "• Bắt buộc xác thực 16-byte GCM Authentication Tag trước khi xuất plaintext.<br/>"
        "• <b>Nếu có bất kỳ bit nào bị sửa &rarr; Ném DecryptionFailedError (TC-05).</b>",
        step_color="#16A34A")
    p3.add_cell('r6', r_step6, card_base, 440, 500, 350, 125)

    r_step7 = build_step_html(7, "Chiếu Trường An toàn (Field Projection)", "GATEWAY",
        "• Gateway đối chiếu danh sách trường được phép xem của Bác sĩ theo ABAC.<br/>"
        "• Lọc bỏ các trường nhạy cảm không thuộc phạm vi thẩm quyền.<br/>"
        "• Trả về Plaintext an toàn cho Bác sĩ trên giao diện xem lâm sàng.",
        step_color="#0284C7")
    p3.add_cell('r7', r_step7, card_base, 65, 500, 290, 125)

    r_step8 = build_step_html(8, "Ghi Vết Truy cập F9", "Z3 AUDIT",
        "• Ghi nhận vết truy cập hồ sơ vào Merkle Audit Log.<br/>"
        "• Lưu trữ: ID Bác sĩ (hashed), ID Hồ sơ, Thời gian, Trạng thái giải mã.",
        step_color="#334155")
    p3.add_cell('r8', r_step8, card_base, 1620, 500, 180, 125)

    # Connecting Edges for Read Flow
    p3.add_edge('re1', 'F1: Query Search', edge_blue, 'r1', 'r2')
    p3.add_edge('re2', 'F4: Blind Index Token', edge_red, 'r2', 'r3')
    p3.add_edge('re3', 'Trả Envelopes + Capsules', edge_amber, 'r3', 'r4')
    p3.add_edge('re4', 'Yêu cầu Unwrap', edge_amber, 'r4', 'r5')
    p3.add_edge('re5', 'Cấp DEK an toàn', edge_green, 'r5', 'r6')
    p3.add_edge('re6', 'Plaintext hợp lệ', edge_blue, 'r6', 'r7')
    p3.add_edge('re7', 'F9 Metadata', edge_gray, 'r6', 'r8')

    # Security Summary Panel for Read
    sec_read_html = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;padding:12px;color:#1E293B;'>"
        "<div style='font-weight:bold;color:#D97706;font-size:12px;margin-bottom:6px;'>CAM KẾT AN TOÀN TRONG QUY TRÌNH ĐỌC (SECURITY INVARIANTS)</div>"
        "<div style='font-size:11px;line-height:1.6;display:grid;grid-template-columns:1fr 1fr;gap:15px;'>"
        "<div>"
        "• <b>Bảo vệ trước Rogue DBA (TC-02):</b> Quản trị viên cơ sở dữ liệu không thể đọc lén dữ liệu qua query trực tiếp vì chỉ thấy Base64 ciphertext vô nghĩa.<br/>"
        "• <b>Phát hiện can thiệp tức thì (TC-05):</b> Bất kỳ hành vi sửa đổi bản mã, hoán đổi tenant_id hay tái sử dụng Nonce đều bị GCM Tag phát hiện và từ chối."
        "</div>"
        "<div>"
        "• <b>Tối thiểu hóa quyền truy cập (Principle of Least Privilege):</b> Bác sĩ chỉ xem được các trường tương ứng với chuyên khoa điều trị (TC-01, TC-24).<br/>"
        "• <b>Chống rò rỉ bộ nhớ:</b> Plaintext và DEK bị xóa khỏi RAM ngay sau khi đóng phiên request."
        "</div></div></div>"
    )
    p3.add_cell('r_sec_box', sec_read_html, card_base, 440, 680, 1360, 120)

    mxfile.append(p3.diagram_elem)


    # =========================================================================
    # TAB 4: CHIA SẺ LIÊN VIỆN CP-ABE & TÍNH TOÁN BFV (ADVANCED CRYPTO)
    # =========================================================================
    p4 = DiagramBuilder('page_adv', '4. Chia sẻ CP-ABE & Tính toán BFV', 1860, 1150)

    h4 = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;text-align:center;color:#0F172A;'>"
        "<div style='font-size:21px;font-weight:800;letter-spacing:0.5px;color:#7C3AED;'>"
        "CƠ CHẾ MẬT MÃ NÂNG CAO: CHIA SẺ CP-ABE &amp; TÍNH TOÁN ĐỒNG CẤU SEAL BFV</div>"
        "<div style='margin-top:4px;font-size:12.5px;color:#475569;'>"
        "Profile P2: Chia sẻ dữ liệu liên viện theo chính sách thuộc tính | Profile P3: Tính tổng bảo mật trên bản mã không cần giải mã"
        "</div></div>"
    )
    p4.add_cell('banner4', h4, card_base, 40, 20, 1780, 65)

    # 2 Big Section Containers
    # Section 1: CP-ABE (Left)
    p4.add_cell('sec_abe', '<b>PHÂN HỆ 1: CHIA SẺ LIÊN VIỆN QUA CP-ABE (PROFILE P2 - AC17 CP-ABE)</b>',
                'rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#A855F7;strokeWidth=2;dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=14;spacingTop=10;fontStyle=1;fontSize=13;fontColor=#6D28D9;',
                40, 105, 870, 980)

    # Section 2: BFV (Right)
    p4.add_cell('sec_bfv', '<b>PHÂN HỆ 2: TÍNH TOÁN ĐỒNG CẤU TRÊN CLOUD (PROFILE P3 - SEAL BFV)</b>',
                'rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDFA;strokeColor=#0D9488;strokeWidth=2;dashed=1;dashPattern=6 4;verticalAlign=top;align=left;spacingLeft=14;spacingTop=10;fontStyle=1;fontSize=13;fontColor=#0F766E;',
                940, 105, 880, 980)

    # Nodes inside Section 1 (CP-ABE)
    p4.add_cell('abe1', build_card_html("1. Khởi tạo Thuộc tính &amp; Khóa Bí mật", [
        "<b>Attribute Authority (AA)</b> thiết lập hệ thống AC17 trên Stanford PBC.",
        "Phát hành Public Parameters (PK) cho các bệnh viện.",
        "Cấp phát <code>User_Secret_Key</code> cho Bác sĩ B dựa trên thuộc tính:<br/>"
        "<code>[HOSPITAL_B, ONCOLOGY_DEPT, DOCTOR_SENIOR]</code>."
    ], header_color="#7C3AED", badge="Z1 AA"), card_base, 70, 160, 390, 130)

    p4.add_cell('abe2', build_card_html("2. Đóng gói &amp; Mã hóa theo Chính sách", [
        "Hospital A muốn chia sẻ hồ sơ bệnh nhân cho khoa Ung bướu BV B.",
        "Gateway mã hóa DEK với chính sách logic cây:<br/>"
        "<code>Policy = (HOSPITAL_B AND ONCOLOGY) OR RESEARCHER</code>.",
        "Tạo ra <code>CP-ABE Capsule</code> lưu kèm gói dữ liệu."
    ], header_color="#7C3AED", badge="ENCRYPT"), card_base, 490, 160, 390, 130)

    p4.add_cell('abe3', build_card_html("3. Lưu trữ &amp; Phân phối Capsule", [
        "Gói chia sẻ gồm <code>FieldEnvelope</code> và <code>CP-ABE Capsule</code>.",
        "Lưu trữ tại Cloud DBMS hoặc phân phối trực tiếp cho bên nhận.",
        "Kẻ tấn công trên mạng hoặc Cloud không thể mở khóa DEK."
    ], header_color="#7C3AED", badge="DISTRIBUTE"), card_base, 70, 340, 390, 120)

    p4.add_cell('abe4', build_card_html("4. Giải mã Ngoại tuyến (Recipient SDK)", [
        "Bác sĩ B tải gói chia sẻ về máy trạm bằng <b>Recipient SDK</b>.",
        "SDK dùng <code>User_Secret_Key</code> để giải mã capsule.",
        "Nếu các thuộc tính thỏa mãn điều kiện logic &rarr; Thu được DEK.",
        "Dùng DEK giải mã hồ sơ bệnh án ngoại tuyến hoàn toàn."
    ], header_color="#7C3AED", badge="DECRYPT SDK"), card_base, 490, 340, 390, 130)

    p4.add_edge('ae1', 'Phát hành Khóa Thuộc tính', edge_purple, 'abe1', 'abe4')
    p4.add_edge('ae2', 'Mã hóa với Policy', edge_purple, 'abe2', 'abe3')
    p4.add_edge('ae3', 'Tải bản mã & Capsule', edge_purple, 'abe3', 'abe4')

    abe_note = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;padding:12px;color:#1E293B;'>"
        "<div style='font-weight:bold;color:#7C3AED;font-size:12px;margin-bottom:6px;'>ƯU THẾ CỦA CP-ABE TRONG Y TẾ (FINE-GRAINED ACCESS)</div>"
        "<div style='font-size:11px;line-height:1.5;'>"
        "• Không cần biết trước danh tính cụ thể của người nhận (Bác sĩ nào trực).<br/>"
        "• Quyền truy cập được gắn liền vào bản mã (Policy-embedded Ciphertext).<br/>"
        "• Thu hồi quyền linh hoạt và không cần kết nối trực tuyến với bên chia sẻ lúc giải mã."
        "</div></div>"
    )
    p4.add_cell('abe_note_box', abe_note, card_base, 70, 520, 810, 110)

    # Nodes inside Section 2 (SEAL BFV)
    p4.add_cell('bfv1', build_card_html("1. Mã hóa Dữ liệu Nghiên cứu (BFV)", [
        "<b>HE Owner (Z1)</b> khởi tạo cặp khóa BFV (Public Key, Secret Key).",
        "Mã hóa các chỉ số định lượng y tế (Tuổi, Liều thuốc, Huyết áp):<br/>"
        "<code>ct_val = BFV.Encrypt(PK, [value_1, value_2, ...])</code>.<br/>"
        "Chỉ gửi bản mã <code>ct_val</code> lên Cloud Worker."
    ], header_color="#0D9488", badge="Z1 HE OWNER"), card_base, 970, 160, 390, 130)

    p4.add_cell('bfv2', build_card_html("2. Tính toán trên Bản mã tại Cloud", [
        "<b>SEAL BFV Worker (Z2)</b> tiếp nhận các bản mã từ nhiều bệnh viện.",
        "Thực hiện phép tính tổng đồng cấu (Homomorphic Addition):<br/>"
        "<code>ct_sum = BFV.Add(ct_1, ct_2, ct_3, ...)</code>.<br/>"
        "Worker hoàn toàn không biết giá trị thực và không thể giải mã!"
    ], header_color="#0D9488", badge="Z2 SEAL WORKER"), card_base, 1400, 160, 390, 130)

    p4.add_cell('bfv3', build_card_html("3. Trả về Kết quả Tổng Mã hóa", [
        "Cloud Worker gửi kết quả mã hóa <code>ct_sum</code> về cho HE Owner.",
        "Không có bất kỳ thông tin riêng tư nào của bệnh nhân bị lộ cho Cloud.",
        "Bảo vệ 100% quyền riêng tư theo tiêu chuẩn y tế quốc tế."
    ], header_color="#0D9488", badge="RESULT"), card_base, 1400, 340, 390, 120)

    p4.add_cell('bfv4', build_card_html("4. Giải mã Thống kê tại Miền Tin cậy", [
        "<b>HE Owner (Z1)</b> dùng Secret Key của mình để giải mã:<br/>"
        "<code>sum_result = BFV.Decrypt(SK, ct_sum)</code>.<br/>"
        "Thu được kết quả thống kê lâm sàng chính xác tuyệt đối mà không vi phạm bảo mật."
    ], header_color="#0D9488", badge="DECRYPT RESULT"), card_base, 970, 340, 390, 130)

    edge_teal = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0D9488;strokeWidth=2;fontColor=#0F766E;fontSize=10;fontStyle=1;'
    p4.add_edge('be1', 'Gửi Ciphertext', edge_teal, 'bfv1', 'bfv2')
    p4.add_edge('be2', 'Tính BFV.Add()', edge_teal, 'bfv2', 'bfv3')
    p4.add_edge('be3', 'Trả ct_sum', edge_teal, 'bfv3', 'bfv4')

    bfv_note = (
        "<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;padding:12px;color:#1E293B;'>"
        "<div style='font-weight:bold;color:#0D9488;font-size:12px;margin-bottom:6px;'>ỨNG DỤNG HOMOMORPHIC ENCRYPTION TRONG Y TẾ (PRIVACY-PRESERVING)</div>"
        "<div style='font-size:11px;line-height:1.5;'>"
        "• Cho phép các bệnh viện hợp tác nghiên cứu dịch tễ học mà không cần chia sẻ dữ liệu gốc.<br/>"
        "• Máy chủ Cloud thực hiện tính toán thống kê nặng nề mà không thể xem trộm hồ sơ.<br/>"
        "• Tuân thủ nghiêm ngặt các quy định HIPAA, GDPR và Nghị định 13/2023/NĐ-CP."
        "</div></div>"
    )
    p4.add_cell('bfv_note_box', bfv_note, card_base, 970, 520, 820, 110)

    mxfile.append(p4.diagram_elem)

    # Serialize XML
    xml_str = ET.tostring(mxfile, encoding='utf-8', xml_declaration=True).decode('utf-8')
    return xml_str

if __name__ == '__main__':
    content = create_all_pages()
    
    out_dir = "/media/howie/Data/Documents/HK1/MH-UD/NT2205.11.CH_Project/docs/diagrams"
    os.makedirs(out_dir, exist_ok=True)
    out_file1 = os.path.join(out_dir, "medshare_system_activity_flow.drawio")
    with open(out_file1, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated: {out_file1} ({len(content)} bytes)")

    out_file2 = "/media/howie/Data/Documents/HK1/MH-UD/NT2205.11.CH_Project/so_do_hoat_dong_he_thong.drawio"
    with open(out_file2, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated: {out_file2} ({len(content)} bytes)")

