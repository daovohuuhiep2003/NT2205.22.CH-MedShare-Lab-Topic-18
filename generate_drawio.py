#!/usr/bin/env python3
"""
Script to generate standard Draw.io XML for MedShare-Lab System Activity & Architecture Flow.
Topic 18: Multi-tenant Healthcare Data Protection over Cloud DBMS.
"""
import html
import os
import xml.etree.ElementTree as ET

def create_drawio_xml():
    # Root structure
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2026-10-07T00:35:00.000Z',
        'agent': 'MedShare-Lab Architectural Modeler',
        'version': '21.0.0',
        'type': 'device'
    })
    
    diagram = ET.SubElement(mxfile, 'diagram', {
        'id': 'medshare-core-activity-flow',
        'name': 'MedShare-Lab System Architecture & Activity Flow'
    })
    
    model = ET.SubElement(diagram, 'mxGraphModel', {
        'dx': '1800',
        'dy': '1200',
        'grid': '1',
        'gridSize': '10',
        'guides': '1',
        'tooltips': '1',
        'connect': '1',
        'arrows': '1',
        'fold': '1',
        'page': '1',
        'pageScale': '1',
        'pageWidth': '1960',
        'pageHeight': '1440',
        'background': '#F8FAFC',
        'math': '0',
        'shadow': '0'
    })
    
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', {'id': '0'})
    ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})

    cell_counter = 100

    def add_cell(cell_id, value, style, x, y, width, height, parent='1', is_vertex=True):
        nonlocal cell_counter
        cid = str(cell_id) if cell_id is not None else str(cell_counter)
        cell_counter += 1
        attrs = {
            'id': cid,
            'value': value,
            'style': style,
            'parent': parent
        }
        if is_vertex:
            attrs['vertex'] = '1'
        cell = ET.SubElement(root, 'mxCell', attrs)
        geo = ET.SubElement(cell, 'mxGeometry', {
            'x': str(x),
            'y': str(y),
            'width': str(width),
            'height': str(height),
            'as': 'geometry'
        })
        return cid

    def add_edge(edge_id, value, style, source, target, waypoints=None, parent='1'):
        nonlocal cell_counter
        eid = str(edge_id) if edge_id is not None else str(cell_counter)
        cell_counter += 1
        attrs = {
            'id': eid,
            'value': value,
            'style': style,
            'parent': parent,
            'edge': '1',
            'source': source,
            'target': target
        }
        cell = ET.SubElement(root, 'mxCell', attrs)
        geo = ET.SubElement(cell, 'mxGeometry', {
            'relative': '1',
            'as': 'geometry'
        })
        if waypoints:
            array = ET.SubElement(geo, 'Array', {'as': 'points'})
            for wx, wy in waypoints:
                ET.SubElement(array, 'mxPoint', {'x': str(wx), 'y': str(wy)})
        return eid

    # ==========================================
    # 1. HEADER BANNER
    # ==========================================
    banner_html = (
        "<div style='font-family: Arial, sans-serif; text-align: center; color: #0F172A;'>"
        "<h1 style='margin: 0; font-size: 22px; font-weight: bold; letter-spacing: 0.5px; color: #1E293B;'>"
        "SƠ ĐỒ KIẾN TRÚC &amp; LUỒNG HOẠT ĐỘNG TOÀN DIỆN HỆ THỐNG MEDSHARE-LAB (TOPIC 18)</h1>"
        "<p style='margin: 4px 0 0 0; font-size: 13px; color: #475569;'>"
        "Bảo vệ dữ liệu y tế đa tenant trên Cloud DBMS qua 4 vùng tin cậy Z0-Z3 | Field Envelope Encryption | ABAC | Blind Index | Vault KMS | CP-ABE | SEAL BFV"
        "</p></div>"
    )
    add_cell("header_banner", banner_html,
             "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;strokeWidth=2;shadow=1;arcSize=8;",
             40, 20, 1880, 75)

    # ==========================================
    # 2. TRUST ZONES (CONTAINERS)
    # ==========================================

    # Z0: User & Endpoint Zone
    z0_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#F0F9FF;strokeColor=#0284C7;strokeWidth=2;"
                "strokeFactor=1;dashed=1;dashPattern=8 4;verticalAlign=top;align=left;spacingLeft=15;"
                "spacingTop=12;fontStyle=1;fontSize=14;fontColor=#0369A1;shadow=0;")
    z0_label = "<b>VÙNG Z0: USER &amp; CLIENT ENDPOINT</b><br/><span style='font-size:10px;font-weight:normal;color:#0284C7;'>Trạm làm việc Bác sĩ / Nhà nghiên cứu / Recipient SDK</span>"
    add_cell("zone_z0", z0_label, z0_style, 40, 115, 330, 800)

    # Z1: Trusted Organizational Zone
    z1_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;strokeWidth=2;"
                "strokeFactor=1;dashed=1;dashPattern=8 4;verticalAlign=top;align=left;spacingLeft=15;"
                "spacingTop=12;fontStyle=1;fontSize=14;fontColor=#15803D;shadow=0;")
    z1_label = "<b>VÙNG Z1: MIỀN TỔ CHỨC TIN CẬY (TRUSTED GATEWAY &amp; KMS)</b><br/><span style='font-size:10px;font-weight:normal;color:#16A34A;'>Nơi duy nhất xử lý Plaintext và giữ DEK trong RAM tạm thời | Ranh giới kiểm soát chính sách ABAC</span>"
    add_cell("zone_z1", z1_label, z1_style, 400, 115, 710, 800)

    # Z2: Untrusted Cloud Zone
    z2_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=2;"
                "strokeFactor=1;dashed=1;dashPattern=8 4;verticalAlign=top;align=left;spacingLeft=15;"
                "spacingTop=12;fontStyle=1;fontSize=14;fontColor=#B91C1C;shadow=0;")
    z2_label = "<b>VÙNG Z2: ĐÁM MÂY KHÔNG TIN CẬY (UNTRUSTED CLOUD DBMS &amp; WORKERS)</b><br/><span style='font-size:10px;font-weight:normal;color:#DC2626;'>Giả định kẻ tấn công có quyền Root OS/DBA | Chỉ lưu Ciphertext, Blind Index &amp; Compute Worker</span>"
    add_cell("zone_z2", z2_label, z2_style, 1140, 115, 780, 800)

    # Z3: Independent Audit Zone
    z3_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#475569;strokeWidth=2;"
                "strokeFactor=1;dashed=1;dashPattern=8 4;verticalAlign=top;align=left;spacingLeft=15;"
                "spacingTop=12;fontStyle=1;fontSize=14;fontColor=#334155;shadow=0;")
    z3_label = "<b>VÙNG Z3: KIỂM TOÁN &amp; GIÁM SÁT ĐỘC LẬP (INDEPENDENT AUDIT &amp; GOVERNANCE)</b><br/><span style='font-size:10px;font-weight:normal;color:#475569;'>Nhật ký bất biến Merkle Hash Chain | Chỉ lưu Metadata F9, tuyệt đối không lưu Plaintext/Key</span>"
    add_cell("zone_z3", z3_label, z3_style, 40, 935, 1880, 140)

    # ==========================================
    # 3. COMPONENTS INSIDE Z0 (Client Zone)
    # ==========================================
    user_style = ("shape=actor;whiteSpace=wrap;html=1;fillColor=#E0F2FE;strokeColor=#0284C7;strokeWidth=2;"
                  "fontColor=#0369A1;fontSize=12;fontStyle=1;align=center;")
    add_cell("c_user", "<b>Bác sĩ / Nhà nghiên cứu</b><br/>(Clinical User / Doctor)", user_style, 140, 165, 80, 80)

    client_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#0284C7;strokeWidth=2;"
                    "fontColor=#0F172A;fontSize=11;align=center;shadow=1;arcSize=10;")
    add_cell("c_portal", "<b>MedShare Web Portal / EMR App</b><br/><span style='font-size:10px;color:#475569;'>Giao diện nghiệp vụ y tế<br/>Gửi truy vấn qua HTTPS / TLS 1.3 (F1)</span>",
             client_style, 65, 280, 275, 75)

    add_cell("c_recipient_sdk", "<b>Recipient SDK (CP-ABE Client)</b><br/><span style='font-size:10px;color:#475569;'>Giải mã Profile P2 (Cross-Tenant)<br/>Sở hữu User Attribute Secret Keys</span>",
             client_style, 65, 460, 275, 85)

    add_cell("c_viewer", "<b>Safe Clinical Viewer</b><br/><span style='font-size:10px;color:#475569;'>Hiển thị Plaintext sau giải mã<br/>Render báo cáo phân tích &amp; chẩn đoán</span>",
             client_style, 65, 620, 275, 75)

    add_cell("c_z0_alert", "<b>[AN TOÀN ĐẦU CUỐI]</b><br/><span style='font-size:9.5px;color:#0284C7;'>Không lưu trữ master key.<br/>Chỉ nhận trường được PDP cấp phép.</span>",
             "rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F2FE;strokeColor=#38BDF8;strokeWidth=1;fontSize=10;align=center;",
             65, 750, 275, 50)

    # ==========================================
    # 4. COMPONENTS INSIDE Z1 (Trusted Gateway & KMS)
    # ==========================================
    # Gateway API + PEP
    gw_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#DCFCE7;strokeColor=#16A34A;strokeWidth=2.5;"
                "fontColor=#14532D;fontSize=12;fontStyle=1;align=center;shadow=1;arcSize=10;")
    add_cell("c_gateway", "<b>TRUSTED CRYPTO GATEWAY</b><br/><span style='font-size:10.5px;font-weight:normal;color:#166534;'>API Entry Point + Policy Enforcement Point (PEP)<br/>Chịu trách nhiệm Session, Điều phối Mã hóa/Giải mã</span>",
             gw_style, 425, 175, 310, 80)

    # Field Cipher Engine
    engine_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#16A34A;strokeWidth=2;"
                    "fontColor=#0F172A;fontSize=11;align=center;shadow=1;arcSize=10;")
    add_cell("c_crypto_engine", "<b>FieldCipherEngine &amp; Blind Index</b><br/><span style='font-size:10px;color:#334155;'>• AES-256-GCM (12-byte CSPRNG Nonce)<br/>• JCS RFC 8785 Canonical AAD Binding<br/>• Blind Index: HMAC-SHA256 Token (F4)</span>",
             engine_style, 425, 295, 310, 85)

    # Key Broker & PEP
    broker_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF9C3;strokeColor=#CA8A04;strokeWidth=2;"
                    "fontColor=#713F12;fontSize=11;align=center;shadow=1;arcSize=10;")
    add_cell("c_key_broker", "<b>Key Broker &amp; Independent PEP</b><br/><span style='font-size:10px;color:#854D0E;'>Kiểm soát quyền truy cập khóa độc lập<br/>Quản lý DEK Scope (Tenant/Data Class)<br/>Yêu cầu Vault Wrap/Unwrap DEK</span>",
             broker_style, 425, 425, 310, 85)

    # Software KMS (HashiCorp Vault Transit)
    kms_style = ("shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;darkOpacity=0.05;"
                 "fillColor=#FDE047;strokeColor=#CA8A04;strokeWidth=2;fontColor=#713F12;fontSize=11;fontStyle=1;align=center;shadow=1;")
    add_cell("c_vault_kms", "<b>Software KMS (HashiCorp Vault)</b><br/><span style='font-size:9.5px;font-weight:normal;color:#854D0E;'>Transit Engine (Port 8200)<br/>Lưu trữ Master KEK &amp; Tenant KEK<br/>Wrap DEK &rarr; KeyCapsule (F0/F8)</span>",
             kms_style, 435, 550, 290, 90)

    # HE / PQC Owner
    add_cell("c_he_pqc_owner", "<b>HE Owner &amp; PQC Archiver</b><br/><span style='font-size:10px;color:#334155;'>Quản lý Secret Key BFV (Microsoft SEAL)<br/>Giải mã Encrypted Aggregates (P3)<br/>Ký số &amp; Mã hóa PQC ML-KEM/ML-DSA (P4)</span>",
             engine_style, 425, 680, 310, 80)

    # Right column in Z1: PDP, IdP, Registry, Attribute Authority, Export Packager
    idp_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#16A34A;strokeWidth=1.5;"
                 "fontColor=#0F172A;fontSize=11;align=center;shadow=1;arcSize=10;")
    add_cell("c_idp", "<b>Identity Provider (IdP) &amp; PIP</b><br/><span style='font-size:10px;color:#475569;'>Xác thực User / OAuth2 / mTLS<br/>Cung cấp vai trò &amp; thuộc tính Bác sĩ</span>",
             idp_style, 780, 175, 295, 75)

    pdp_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#DCFCE7;strokeColor=#15803D;strokeWidth=2.5;"
                 "fontColor=#14532D;fontSize=12;fontStyle=1;align=center;shadow=1;arcSize=10;")
    add_cell("c_pdp", "<b>PDP (Policy Decision Point)</b><br/><span style='font-size:10.5px;font-weight:normal;color:#166534;'>Động cơ ABAC Độc lập (Deny-by-Default)<br/>Đánh giá Subject, Object, Action, Environment (F2)</span>",
             pdp_style, 780, 290, 295, 85)

    add_cell("c_registry", "<b>Trusted Manifest Registry</b><br/><span style='font-size:10px;color:#475569;'>Lưu Schema hồ sơ, Phiên bản KEK/DEK<br/>Freshness Check &amp; Hash Integrity Manifest (F8)</span>",
             idp_style, 780, 420, 295, 80)

    add_cell("c_aa", "<b>Attribute Authority (AA - CP-ABE)</b><br/><span style='font-size:10px;color:#475569;'>Quản lý Master Secret Key AC17<br/>Cấp phát User Secret Keys theo thuộc tính<br/>Xuất Public Parameters cho Encryptor</span>",
             idp_style, 780, 540, 295, 85)

    add_cell("c_export", "<b>Cohort Packager &amp; PQC Signer</b><br/><span style='font-size:10px;color:#475569;'>Đóng gói hồ sơ nghiên cứu liên viện<br/>Ký số FIPS 204 ML-DSA-65 chống giả mạo</span>",
             idp_style, 780, 675, 295, 80)

    # ==========================================
    # 5. COMPONENTS INSIDE Z2 (Untrusted Cloud Zone)
    # ==========================================
    # Cloud Storage (Postgres & Mongo)
    db_style = ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;"
                "fillColor=#FEE2E2;strokeColor=#DC2626;strokeWidth=2.5;fontColor=#7F1D1D;fontSize=12;fontStyle=1;align=center;shadow=1;")
    add_cell("c_cloud_db", "<b>UNTRUSTED CLOUD DBMS</b><br/><span style='font-size:10px;font-weight:normal;color:#991B1B;'>"
                           "<b>PostgreSQL 16</b> (Port 5432) &amp; <b>MongoDB 7.0</b> (Port 27017)<br/>"
                           "• Chứa <b>FieldEnvelope</b> (Ciphertext Base64 + Auth Tag)<br/>"
                           "• Chứa <b>KeyCapsule</b> (Wrapped DEK bởi KEK)<br/>"
                           "• Chứa <b>Blind Index Token</b> (HMAC Token tra cứu điểm)</span>",
             db_style, 1170, 165, 360, 140)

    # Cloud Replicas / Backups
    replica_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=1.5;"
                     "fontColor=#0F172A;fontSize=11;align=center;shadow=1;arcSize=10;")
    add_cell("c_cloud_replicas", "<b>Cloud Replicas &amp; Snapshots (CDC)</b><br/><span style='font-size:10px;color:#475569;'>WAL Stream / Oplog Replications<br/>Bản sao lưu Volume (Chỉ chứa Ciphertext, chống TC-08)</span>",
             replica_style, 1575, 175, 305, 120)

    # Cryptographic Workers
    worker_box_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#EF4444;strokeWidth=2;"
                        "fontColor=#991B1B;fontSize=11;align=center;shadow=1;arcSize=10;")
    
    add_cell("c_abe_worker", "<b>Docker Worker: CP-ABE (AC17)</b><br/><span style='font-size:10px;color:#475569;'>Stanford PBC 0.5.14 + Charm-Crypto<br/>Mã hóa Capsule theo Policy liên viện</span>",
             worker_box_style, 1170, 360, 340, 85)

    add_cell("c_pqc_worker", "<b>Docker Worker: PQC (liboqs)</b><br/><span style='font-size:10px;color:#475569;'>FIPS 203 ML-KEM-768 &amp; FIPS 204 ML-DSA-65<br/>Đóng gói &amp; Ký số an toàn hậu lượng tử</span>",
             worker_box_style, 1555, 360, 325, 85)

    add_cell("c_he_worker", "<b>Docker Worker: Homomorphic (SEAL BFV)</b><br/><span style='font-size:10px;color:#475569;'>Microsoft SEAL v4.1.2 BFV C++17<br/>Tính Encrypted Sum trực tiếp trên Ciphertext (F6)</span>",
             worker_box_style, 1170, 495, 340, 95)

    # Adversary Threat Model Box
    threat_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FEE2E2;strokeColor=#B91C1C;strokeWidth=2.5;"
                    "dashed=1;fontColor=#7F1D1D;fontSize=11;align=center;shadow=1;arcSize=10;")
    add_cell("c_threat_box", "<b>MÔ HÌNH KẺ TẤN CÔNG (THREAT MODEL Z2)</b><br/><span style='font-size:10px;color:#991B1B;'>"
                             "<b>Rogue DBA / Malicious Cloud Admin</b><br/>"
                             "• Thực hiện Direct Query Bypass (TC-02): <i>Chỉ thấy Ciphertext vô nghĩa!</i><br/>"
                             "• Thực hiện Bit-Flipping / Tampering (TC-05): <i>Bị chặn bởi GCM Tag &amp; JCS AAD!</i><br/>"
                             "• Thao túng Volume Snapshot (TC-08): <i>Không có KEK để giải mã!</i></span>",
             threat_style, 1555, 480, 325, 140)

    # ==========================================
    # 6. COMPONENTS INSIDE Z3 (Audit & Governance Zone)
    # ==========================================
    audit_style = ("rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#475569;strokeWidth=2;"
                   "fontColor=#0F172A;fontSize=11;align=center;shadow=1;arcSize=10;")
    
    add_cell("c_audit_log", "<b>Append-Only Audit Log (Merkle Chained)</b><br/><span style='font-size:10px;color:#334155;'>Ghi nhận vết truy cập F9: <code>[op_id, subject_hash, policy_ver, kek_id, digest]</code><br/>Bảo đảm tính toàn vẹn và không thể bị chối bỏ</span>",
             audit_style, 80, 975, 540, 75)

    add_cell("c_witness", "<b>External Checkpoint Witness &amp; Notary</b><br/><span style='font-size:10px;color:#334155;'>Ký số định kỳ trên Root Hash của Merkle Audit Tree<br/>Kiểm toán viên độc lập xác minh tính toàn vẹn (Out-of-band)</span>",
             audit_style, 680, 975, 540, 75)

    add_cell("c_siem", "<b>Security Monitoring &amp; Tamper Alerting</b><br/><span style='font-size:10px;color:#334155;'>Phát hiện truy cập bất thường, từ chối giải mã hàng loạt<br/>Cảnh báo tức thời nếu phát hiện vi phạm ranh giới Z1/Z2</span>",
             audit_style, 1280, 975, 590, 75)

    # ==========================================
    # 7. WORKFLOW EDGES (CONNECTORS WITH STYLES)
    # ==========================================
    # Style definitions
    style_f1 = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0284C7;strokeWidth=2;fontColor=#0369A1;fontSize=10;fontStyle=1;"
    style_write = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16A34A;strokeWidth=2.5;fontColor=#15803D;fontSize=10;fontStyle=1;"
    style_read = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#D97706;strokeWidth=2.5;fontColor=#B45309;fontSize=10;fontStyle=1;"
    style_share = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7C3AED;strokeWidth=2;fontColor=#6D28D9;fontSize=10;fontStyle=1;"
    style_audit = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.5;dashed=1;fontColor=#334155;fontSize=9;"

    # 7.1 Luồng Client -> Gateway (F1)
    add_edge("e_user_portal", "Thao tác EMR", style_f1, "c_user", "c_portal")
    add_edge("e_portal_gw", "<b>[1] F1: Yêu cầu Đọc / Ghi (TLS 1.3 + JWT)</b>", style_f1, "c_portal", "c_gateway")

    # 7.2 Luồng Xác thực & ABAC (F2)
    add_edge("e_gw_idp", "Xác thực danh tính", style_f1, "c_gateway", "c_idp")
    add_edge("e_gw_pdp", "<b>[2] F2: ABAC Context (Subject/Object/Env)</b>", style_write, "c_gateway", "c_pdp")
    add_edge("e_pdp_gw", "<b>Permit / Deny (Deny-by-default)</b>", style_write, "c_pdp", "c_gateway", waypoints=[(770, 250), (740, 250)])

    # 7.3 Luồng Cấp phát & Bọc khóa DEK (F0/F8)
    add_edge("e_gw_engine", "Truyền Plaintext cần mã hóa", style_write, "c_gateway", "c_crypto_engine")
    add_edge("e_engine_broker", "Yêu cầu DEK cho Tenant/DataClass", style_write, "c_crypto_engine", "c_key_broker")
    add_edge("e_broker_pdp", "Kiểm tra quyền truy cập khóa", style_write, "c_key_broker", "c_pdp")
    add_edge("e_broker_reg", "Kiểm tra phiên bản KEK (F8)", style_write, "c_key_broker", "c_registry")
    add_edge("e_broker_kms", "<b>[3] F0: Wrap DEK &rarr; KeyCapsule</b>", style_write, "c_key_broker", "c_vault_kms")
    add_edge("e_kms_broker", "Trả về KeyCapsule + DEK an toàn", style_write, "c_vault_kms", "c_key_broker")

    # 7.4 Luồng Ghi xuống Cloud DB (F3, F4)
    add_edge("e_engine_db", "<b>[4] F3: Ghi Ciphertext (FieldEnvelope + KeyCapsule + BlindIndex)</b>",
             style_write, "c_crypto_engine", "c_cloud_db", waypoints=[(740, 340), (1160, 240)])
    add_edge("e_db_replicas", "F7: Replicas / CDC", style_audit, "c_cloud_db", "c_cloud_replicas")

    # 7.5 Luồng Đọc & Tra Cứu (R1 - R8)
    add_edge("e_gw_db_read", "<b>[R1] F4: Tra cứu theo Blind Index Token (HMAC)</b>",
             style_read, "c_gateway", "c_cloud_db", waypoints=[(740, 200), (1160, 200)])
    add_edge("e_db_gw_fetch", "<b>[R2] Trả về Ciphertext Envelope + KeyCapsule</b>",
             style_read, "c_cloud_db", "c_crypto_engine", waypoints=[(1160, 270), (750, 310)])
    add_edge("e_broker_unwrap", "<b>[R3] Unwrap DEK qua Vault KMS (Validated Context)</b>",
             style_read, "c_key_broker", "c_vault_kms")
    add_edge("e_engine_verify", "<b>[R4] Xác thực AAD &amp; Tag &rarr; Giải mã Plaintext</b>",
             style_read, "c_crypto_engine", "c_gateway")
    add_edge("e_gw_viewer", "<b>[R5] Trả Plaintext các trường được phép</b>",
             style_read, "c_gateway", "c_viewer", waypoints=[(410, 220), (350, 650)])

    # 7.6 Luồng Chia sẻ liên viện CP-ABE (Profile P2)
    add_edge("e_aa_sdk", "Cấp User Attribute Secret Keys", style_share, "c_aa", "c_recipient_sdk", waypoints=[(770, 580), (350, 500)])
    add_edge("e_gw_abe_worker", "Mã hóa DEK với Policy liên viện", style_share, "c_gateway", "c_abe_worker", waypoints=[(745, 230), (1160, 400)])
    add_edge("e_db_sdk_share", "Tải Encrypted Package &amp; Capsule", style_share, "c_cloud_db", "c_recipient_sdk", waypoints=[(1160, 290), (350, 470)])

    # 7.7 Luồng Tính toán Đồng cấu BFV (Profile P3)
    add_edge("e_he_owner_worker", "F6: Gửi BFV Encrypted Cohort Data", style_share, "c_he_pqc_owner", "c_he_worker")
    add_edge("e_he_worker_owner", "Trả về Encrypted Aggregate (SUM)", style_share, "c_he_worker", "c_he_pqc_owner", waypoints=[(1160, 550), (745, 730)])

    # 7.8 Luồng PQC Archive (Profile P4)
    add_edge("e_export_pqc", "Ký số ML-DSA-65 &amp; Đóng gói PQC", style_share, "c_export", "c_pqc_worker")

    # 7.9 Luồng Ghi Audit Log F9 sang Z3
    add_edge("e_gw_audit", "<b>F9: Gateway Audit Log</b>", style_audit, "c_gateway", "c_audit_log", waypoints=[(420, 240), (200, 965)])
    add_edge("e_pdp_audit", "<b>F9: Policy Decision Log</b>", style_audit, "c_pdp", "c_audit_log", waypoints=[(770, 350), (320, 965)])
    add_edge("e_broker_audit", "<b>F9: Key-Use Log</b>", style_audit, "c_key_broker", "c_audit_log", waypoints=[(420, 480), (450, 965)])
    add_edge("e_audit_witness", "Checkpoint Merkle Hash", style_audit, "c_audit_log", "c_witness")
    add_edge("e_witness_siem", "Đối soát &amp; Cảnh báo", style_audit, "c_witness", "c_siem")

    # ==========================================
    # 8. LEGEND & WORKFLOW SUMMARY PANELS (BOTTOM)
    # ==========================================
    # Card 1: Luồng Ghi
    card_write = (
        "<div style='font-family: Arial, sans-serif; font-size: 11px; color: #1E293B;'>"
        "<div style='font-weight: bold; color: #15803D; font-size: 12px; margin-bottom: 4px; border-bottom: 2px solid #16A34A; padding-bottom: 2px;'>"
        "1. QUY TRÌNH GHI HỒ SƠ Y TẾ (WRITE / ENVELOPE INGESTION)"
        "</div>"
        "<ol style='margin: 0; padding-left: 18px; line-height: 1.45;'>"
        "<li><b>Yêu cầu:</b> Client gửi hồ sơ bệnh án qua HTTPS/TLS 1.3 kèm JWT xác thực (F1).</li>"
        "<li><b>Kiểm tra ABAC:</b> Gateway PEP gửi Context sang PDP. Deny-by-default kiểm tra quyền ghi (F2).</li>"
        "<li><b>Cấp phát DEK:</b> Key Broker sinh DEK ngẫu nhiên (CSPRNG 256-bit) cho Tenant + Data Class.</li>"
        "<li><b>Bọc khóa (Wrap):</b> Key Broker gọi Vault KMS bọc DEK bằng KEK &rarr; <code>KeyCapsule</code>.</li>"
        "<li><b>Mã hóa trường:</b> FieldCipherEngine mã hóa AES-256-GCM với Nonce 12B, ràng buộc RFC 8785 JCS AAD.</li>"
        "<li><b>Blind Index:</b> Sinh HMAC-SHA256 Token cho các trường tra cứu chính xác (F4).</li>"
        "<li><b>Lưu trữ Cloud:</b> Lưu Envelope + Capsule + Blind Index xuống PostgreSQL / MongoDB (F3).</li>"
        "<li><b>Ghi vết Z3:</b> Ghi F9 Audit Log (Metadata only, tuyệt đối không ghi Plaintext hay Key).</li>"
        "</ol>"
        "</div>"
    )
    add_cell("card_write_flow", card_write,
             "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#16A34A;strokeWidth=1.5;shadow=1;align=left;spacing=10;arcSize=6;",
             40, 1090, 450, 240)

    # Card 2: Luồng Đọc
    card_read = (
        "<div style='font-family: Arial, sans-serif; font-size: 11px; color: #1E293B;'>"
        "<div style='font-weight: bold; color: #D97706; font-size: 12px; margin-bottom: 4px; border-bottom: 2px solid #D97706; padding-bottom: 2px;'>"
        "2. QUY TRÌNH ĐỌC &amp; TRA CỨU BẢO MẬT (READ / SEARCH FLOW)"
        "</div>"
        "<ol style='margin: 0; padding-left: 18px; line-height: 1.45;'>"
        "<li><b>Truy vấn:</b> Bác sĩ yêu cầu xem hồ sơ bệnh nhân theo CCCD/Mã bệnh án (F1).</li>"
        "<li><b>ABAC &amp; Blind Token:</b> Gateway kiểm tra PDP; sinh HMAC Blind Index Token tra cứu điểm.</li>"
        "<li><b>Tìm kiếm Cloud DB:</b> Cloud DB dùng Blind Index tìm bản ghi &rarr; trả về Ciphertext Envelope + Capsule.</li>"
        "<li><b>Yêu cầu gỡ khóa:</b> Gateway gửi KeyCapsule và Expected Context sang Key Broker.</li>"
        "<li><b>Gỡ khóa (Unwrap):</b> Key Broker kiểm tra PDP &amp; Registry, gọi Vault KMS gỡ DEK an toàn.</li>"
        "<li><b>Xác thực &amp; Giải mã:</b> FieldCipherEngine bắt buộc xác thực AAD &amp; GCM Auth Tag trước khi xuất Plaintext.</li>"
        "<li><b>Lọc quyền trả về:</b> Gateway chỉ trả về các trường Plaintext được PDP cho phép (TC-01, TC-24).</li>"
        "<li><b>Ghi vết Z3:</b> Ghi lại Operation ID và Subject Hash vào Audit Log Merkle Tree (F9).</li>"
        "</ol>"
        "</div>"
    )
    add_cell("card_read_flow", card_read,
             "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=1.5;shadow=1;align=left;spacing=10;arcSize=6;",
             505, 1090, 450, 240)

    # Card 3: Chia sẻ & Tính toán đồng cấu
    card_adv = (
        "<div style='font-family: Arial, sans-serif; font-size: 11px; color: #1E293B;'>"
        "<div style='font-weight: bold; color: #7C3AED; font-size: 12px; margin-bottom: 4px; border-bottom: 2px solid #7C3AED; padding-bottom: 2px;'>"
        "3. CHIA SẺ LIÊN VIỆN &amp; TÍNH TOÁN BẢO MẬT (PROFILES P2 - P4)"
        "</div>"
        "<ul style='margin: 0; padding-left: 18px; line-height: 1.45;'>"
        "<li><b>CP-ABE Sharing (Profile P2):</b>"
        "<br/>- Attribute Authority (AA) phát hành Secret Key cho Bác sĩ nhận dựa trên thuộc tính vai trò."
        "<br/>- Gateway mã hóa DEK với chính sách logic <code>(HOSPITAL_B AND ONCOLOGY)</code>."
        "<br/>- Người nhận tự giải mã ngoại tuyến (Offline) bằng Recipient SDK khi thỏa mãn chính sách.</li>"
        "<li><b>Homomorphic Computation (Profile P3 - SEAL BFV):</b>"
        "<br/>- Dữ liệu nghiên cứu được mã hóa đồng cấu gửi tới BFV Worker (Z2)."
        "<br/>- Cloud Worker tính toán tổng (SUM) trực tiếp trên bản mã mà không biết giá trị thực."
        "<br/>- HE Owner (Z1) giữ Secret Key thực hiện giải mã kết quả thống kê.</li>"
        "<li><b>Post-Quantum Archival (Profile P4 - ML-KEM / ML-DSA):</b>"
        "<br/>- Đóng gói dữ liệu lưu trữ dài hạn chống mối đe dọa Harvest-Now-Decrypt-Later.</li>"
        "</ul>"
        "</div>"
    )
    add_cell("card_adv_flow", card_adv,
             "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#7C3AED;strokeWidth=1.5;shadow=1;align=left;spacing=10;arcSize=6;",
             970, 1090, 450, 240)

    # Card 4: Threat Model & Ranh giới an toàn
    card_security = (
        "<div style='font-family: Arial, sans-serif; font-size: 11px; color: #1E293B;'>"
        "<div style='font-weight: bold; color: #DC2626; font-size: 12px; margin-bottom: 4px; border-bottom: 2px solid #DC2626; padding-bottom: 2px;'>"
        "4. MÔ HÌNH ĐE DỌA &amp; KIỂM CHỨNG AN TOÀN (SECURITY ASSURANCE)"
        "</div>"
        "<ul style='margin: 0; padding-left: 18px; line-height: 1.45;'>"
        "<li><b>Rogue DBA / Query Bypass (TC-02):</b> Kẻ quản trị Cloud DB truy vấn trực tiếp chỉ thấy Base64 Ciphertext. Không thể truy cập Vault KMS (Z1) để giải mã.</li>"
        "<li><b>Tamper &amp; Bit-Flipping Attack (TC-05):</b> Mọi hành vi sửa đổi Ciphertext, Nonce, hoặc hoán đổi Tenant ID trong AAD đều làm hỏng GCM Auth Tag &rarr; Lập tức kích hoạt <code>DecryptionFailedError</code> fail-closed!</li>"
        "<li><b>Snapshot Theft (TC-08):</b> Bản sao lưu đĩa đạt entropy cực đại (~7.997 bits/byte), không rò rỉ Plaintext khi mất ổ cứng.</li>"
        "<li><b>Multi-tenant Boundary (TC-06):</b> Khóa KEK phân tách độc lập giữa các bệnh viện. Không một tenant nào unwrap được DEK của tenant khác.</li>"
        "<li><b>Audit Tamper Resistance:</b> Nhật ký Merkle Tree tại Z3 được ký số bởi External Witness, ngăn chặn xóa vết tích tấn công.</li>"
        "</ul>"
        "</div>"
    )
    add_cell("card_security_flow", card_security,
             "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#DC2626;strokeWidth=1.5;shadow=1;align=left;spacing=10;arcSize=6;",
             1435, 1090, 485, 240)

    # ==========================================
    # 9. EXPORT XML
    # ==========================================
    xml_str = ET.tostring(mxfile, encoding='utf-8', xml_declaration=True).decode('utf-8')
    return xml_str

if __name__ == '__main__':
    content = create_drawio_xml()
    # Write to docs/diagrams/
    out_dir = "/media/howie/Data/Documents/HK1/MH-UD/NT2205.11.CH_Project/docs/diagrams"
    os.makedirs(out_dir, exist_ok=True)
    out_file1 = os.path.join(out_dir, "medshare_system_activity_flow.drawio")
    with open(out_file1, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated: {out_file1} ({len(content)} bytes)")

    # Also write to root for convenience
    out_file2 = "/media/howie/Data/Documents/HK1/MH-UD/NT2205.11.CH_Project/so_do_hoat_dong_he_thong.drawio"
    with open(out_file2, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated: {out_file2} ({len(content)} bytes)")

