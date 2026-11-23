Dưới đây là các nguồn dataset ảnh y khoa công khai, chia theo loại. Hầu hết miễn phí, nhưng một số cần đăng ký hoặc có điều khoản chỉ dùng cho nghiên cứu/giảng dạy.

## X-quang (đặc biệt là X-quang ngực)

- **NIH ChestX-ray14**: 112.120 ảnh X-quang ngực thẳng từ 30.805 bệnh nhân, gắn 14 nhãn bệnh lý nhị phân. Tải trực tiếp tại NIH Box: https://nihcc.app.box.com/v/ChestXray-NIHCC. Đây cũng là bộ có trên Google Cloud public storage, và có bản mirror trên Kaggle.
- **CheXpert (Stanford)**: 224.316 ảnh X-quang ngực của 65.240 bệnh nhân, kèm báo cáo chẩn đoán. Có bản nhỏ "CheXpert-v1.0-small" trên Kaggle để thử nhanh.
- **MIMIC-CXR / MIMIC-CXR-JPG (PhysioNet)**: 377.110 ảnh thuộc 227.835 ca chụp, kèm báo cáo dạng văn bản. Bản gốc là DICOM, bản JPG tiện hơn. Lưu ý bộ đầy đủ yêu cầu đăng ký xin quyền truy cập trên PhysioNet.
- **VinDr-CXR** (bệnh viện ở Việt Nam): 18.000 ảnh, gán nhãn thủ công. Bộ này nên quan tâm vì dữ liệu có nguồn gốc Việt Nam.
- **MURA** (xương khớp): 40.561 ảnh X-quang đa góc nhìn, gán nhãn bình thường/bất thường bởi bác sĩ.
- **COVID-19 Radiography Dataset**: hơn 21.000 ảnh X-quang và CT, miễn phí.

## Siêu âm

- **BUSI** (siêu âm vú): 780 ảnh chia 3 nhóm: lành tính, ác tính, bình thường, có trên Kaggle, kèm mask phân vùng. Dung lượng nhỏ nên rất hợp để thử nghiệm.
- **BUS-BRA**: ảnh siêu âm vú ẩn danh của 1.064 bệnh nhân, có phân loại BI-RADS. Tải tại Zenodo: https://zenodo.org/record/7730708
- **HC18**: 1.344 ảnh siêu âm đầu thai nhi để đo chu vi đầu, giấy phép CC BY 4.0.
- **CAMUS** (siêu âm tim) và **Ultrasound Nerve Segmentation** (Kaggle): có chú thích ở mức pixel cho bài toán phân vùng.
- **RadImageNet-US**: khoảng 390 nghìn ảnh, 15 cấu trúc vùng bụng, nhưng giấy phép thương mại có thể hạn chế.

## CT, MRI và file DICOM mẫu

- **TCIA (The Cancer Imaging Archive)**: kho lớn nhất cho CT, MRI, PET dạng DICOM, 100+ bộ sưu tập, có mask phân vùng. Cũng có một số bộ siêu âm (ví dụ siêu âm tuyến tiền liệt kết hợp MRI). Có thể tải riêng từng ca, không cần tải cả bộ hàng trăm GB.
- **MedPix (NLM)**: hơn 59.000 ảnh từ khoảng 12.000 bệnh nhân, gồm X-quang, CT, MRI, thiên về giáo dục.
- **OsiriX DICOM sample sets**: file DICOM mẫu để học và test phần mềm. Chỉ dùng cho nghiên cứu và giảng dạy, không được phân phối lại hay dùng thương mại.
- **Zenodo (record 13932977)**: gói ~326 MB gồm MRI T1, CT, X-quang số dạng DICOM, ảnh siêu âm, phù hợp để tập đọc file bằng SimpleITK.
- **Medical Segmentation Decathlon**, **OpenNeuro** (MRI não), **OASIS**: dùng cho phân vùng và thần kinh.

## Gợi ý để bắt đầu nhanh

1. Muốn thử nhanh, ít dung lượng: BUSI (siêu âm), CheXpert-small (X-quang) trên Kaggle.
2. Muốn học định dạng DICOM: OsiriX samples hoặc gói Zenodo ở trên.
3. Muốn làm nghiên cứu nghiêm túc: TCIA, MIMIC-CXR, VinDr-CXR.

Lưu ý: dù đã ẩn danh, các bộ này vẫn có điều khoản sử dụng (trích dẫn, không dùng thương mại, không phân phối lại), nên bạn nên đọc license trước khi dùng.

Bạn định dùng để làm gì (huấn luyện mô hình AI, test phần mềm đọc DICOM, hay học tập)? Mình có thể thu hẹp lại và hướng dẫn cách tải cụ thể.