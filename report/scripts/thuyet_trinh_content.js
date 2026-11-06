// Nội dung dùng chung cho kịch bản đọc (.docx) và slide (.pptx), bản viết cho người nghe không làm kỹ thuật.
// Slide: mỗi slide một ý, tiêu đề là câu kết luận, tối đa 3 dòng ngắn hoặc 1 con số lớn hoặc 1 hình.
// Lời nói (script) chi tiết, thuật ngữ luôn kèm giải thích bằng lời thường.
// Số liệu: mô hình đang phục vụ trên nhánh publish/salary-ml (1.735 tin thật, artifacts/salary-v2).
//
// Trường của một slide:
//   layout: "cover" | "section" | "big" | "points" | "compare" (mặc định "points")
//   title, subtitle, big {value, caption}, points [..], compare {left:{head, lines}, right:{head, lines}},
//   fig (đường dẫn từ report/), note (một dòng nhỏ cuối slide), script [đoạn lời nói]

const SLIDES = [
  // ───────────────────────── MỞ ĐẦU
  {
    section: "Mở đầu",
    layout: "cover",
    title: "Lương ngành IT ở Việt Nam: thị trường đang trả bao nhiêu, và nên học gì để tăng lương?",
    subtitle: "Tiểu luận Lập trình Python – Đề tài 4 · Nhóm 3\nGVHD: ThS. Lý Ngọc Hưng · Trường Đại học Gia Định",
    script: [
      "Em chào thầy và các bạn. Đề tài của em là phân tích thị trường việc làm ngành công nghệ thông tin và dự đoán mức lương lập trình viên.",
      "Em xin nói trước cách em trình bày. Trong dự án này, gần như mỗi quyết định đều đến từ một vấn đề cụ thể mà nhóm gặp phải ở bước trước. Nên với mỗi phần, em sẽ kể theo đúng một mạch: trước đó xảy ra chuyện gì, nếu để nguyên thì hậu quả là gì, nhóm đã chọn cách nào và vì sao, và cái giá phải trả là gì. Em sẽ cố giải thích bằng ví dụ đời thường, những từ chuyên môn em sẽ giải thích ngay khi nhắc tới.",
    ],
  },
  {
    section: "Mở đầu",
    title: "Ba câu hỏi người đi làm IT hay đặt ra",
    points: ["Công nghệ nào đang được tuyển nhiều?", "Lương của tôi đang cao hay thấp so với thị trường?", "Nên học thêm gì để tăng lương?"],
    script: [
      "Bắt đầu từ người dùng. Một bạn sinh viên sắp ra trường, hay một lập trình viên đã đi làm vài năm, thường có ba câu hỏi. Công nghệ nào đang được tuyển nhiều. Lương của mình đang cao hay thấp so với thị trường. Và nên học thêm gì để được trả cao hơn.",
      "Câu trả lời thật ra đã nằm sẵn trong hàng nghìn tin tuyển dụng trên TopCV, ITviec, VietnamWorks. Mỗi tin đều ghi lương, kinh nghiệm, kỹ năng cần có. Việc của nhóm là đọc hết những tin đó, biến chúng thành số liệu đáng tin, rồi xây một công cụ trả lời ba câu hỏi này.",
      "Đề bài yêu cầu năm phần: làm sạch dữ liệu bằng Pandas và NumPy, vẽ biểu đồ bằng Matplotlib và Seaborn, xây và so sánh ít nhất hai mô hình dự đoán, chỉ ra kỹ năng nào làm tăng thu nhập, và làm một ứng dụng tư vấn. Em sẽ đi lần lượt qua từng phần.",
    ],
  },

  // ───────────────────────── PHẦN 1: DỮ LIỆU
  { section: "Phần 1 · Dữ liệu", layout: "section", title: "Phần 1\nDữ liệu: từ tin tuyển dụng lộn xộn đến số liệu đáng tin", script: ["Phần một là dữ liệu. Đây là phần tốn nhiều công sức nhất, và cũng là phần có nhiều bài học nhất."] },
  {
    section: "Phần 1 · Dữ liệu",
    layout: "big",
    title: "Nguyên liệu: 8.523 tin tuyển dụng công khai",
    big: { value: "8.523", caption: "tin IT từ TopCV, ITviec, VietnamWorks, CareerViet, CareerBuilder" },
    note: "Ba bộ dữ liệu công khai trên Kaggle, thu thập năm 2023 và 2026",
    script: [
      "Nguyên liệu là ba bộ dữ liệu công khai trên Kaggle, gồm 8.523 tin tuyển dụng ngành IT, lấy từ năm trang tuyển dụng lớn ở Việt Nam.",
      "Ba bộ này mỗi bộ ghi theo một kiểu khác nhau: bộ thì có mô tả công việc, bộ thì chỉ có tên vị trí, bộ thì mô tả còn dính mã HTML của trang web. Nên việc đầu tiên là đưa cả ba về cùng một mẫu: tên vị trí, công ty, địa điểm, lương, kinh nghiệm và kỹ năng.",
    ],
  },
  {
    section: "Phần 1 · Dữ liệu",
    title: "Dữ liệu thô rất lộn xộn",
    points: [
      "36% tin chỉ ghi “Thỏa thuận”, không có con số",
      "Cùng là lương nhưng có hơn 30 kiểu ghi: “15–25 triệu”, “Tới 30 triệu”, “$1.000”",
      "“1 triệu – 40 triệu”: con số mặc định của trang web, không phải lương thật",
    ],
    script: [
      "Khi mở dữ liệu thô ra, vấn đề hiện ra ngay. Thứ nhất, 36% số tin chỉ ghi \"Thỏa thuận\" hay \"Cạnh tranh\", không có con số nào. Những tin này không thể dùng để dạy máy đoán lương, nhưng vẫn dùng được để đếm kỹ năng nào được tuyển nhiều.",
      "Thứ hai, cùng là lương nhưng có hơn 30 cách ghi khác nhau: \"15 đến 25 triệu\", \"Tới 30 triệu\", \"1.000 đô\", có tin ghi lương năm. Có cả lỗi chính tả như \"triẹu\" với dấu nặng đặt sai. Con người đọc thì hiểu, máy thì không. Nếu không quy đổi, một tin \"1.000 đô\" sẽ bị hiểu là 1.000 triệu đồng.",
      "Thứ ba, và đây là loại lỗi nguy hiểm nhất: có 111 tin ghi đúng một chuỗi \"1 triệu đến 40 triệu\". Đó không phải lương thật mà là giá trị mặc định của biểu mẫu khi nhà tuyển dụng không muốn công bố. Nếu lấy điểm giữa thì được 20,5 triệu, một con số trông rất bình thường. Máy sẽ không báo lỗi gì cả, nó chỉ lặng lẽ học sai.",
    ],
  },
  {
    section: "Phần 1 · Dữ liệu",
    title: "Mỗi quy tắc xử lý đều có lý do đời thường",
    points: [
      "Tin ghi khoảng → lấy điểm giữa: “15–25 triệu” = khoảng 20 triệu",
      "“Tới 30 triệu” → đoán đầu dưới theo thói quen ghi lương của từng trang",
      "Khoảng chênh hơn 3 lần → bỏ, vì đó là cách né công bố lương",
    ],
    script: [
      "Với mỗi lỗi, nhóm đặt một quy tắc, và mỗi quy tắc đều có lý do.",
      "Một tin ghi \"15 đến 25 triệu\" thì máy cần một con số. Nhóm cân nhắc lấy đầu dưới, đầu trên, hay điểm giữa. Đầu dưới thì thiên thấp. Đầu trên giống \"mức trần\", ít người được nhận. Nhóm chọn điểm giữa, 20 triệu, vì đó chính là cách nhà tuyển dụng hay nói: \"lương khoảng 20 triệu\".",
      "Một tin chỉ ghi \"Tới 30 triệu\" thì sao? Nếu coi là 30 triệu thì thổi phồng, vì đó là mức trần. Ban đầu nhóm đoán đầu dưới bằng 70% đầu trên. Nhưng khi kiểm tra kỹ, nhóm thấy mỗi trang tuyển dụng có thói quen ghi khoảng lương khác nhau: ITviec hay ghi khoảng hẹp, TopCV hay ghi khoảng rộng. Nên nhóm đổi sang học thói quen của từng trang từ chính những tin ghi đủ hai đầu. Ví dụ với TopCV, \"Tới 30 triệu\" được hiểu là khoảng 20 đến 30 triệu. Giống một người quen thị trường sẽ nói: tin TopCV ghi \"tới 30\" thì thường là từ 20.",
      "Còn khoảng lương chênh hơn 3 lần như \"1 đến 40 triệu\" thì bị bỏ. Ngoài đời, một vị trí hiếm khi trả chênh nhau quá 3 lần giữa mức thấp và mức cao; khoảng rộng như vậy chỉ là cách né công bố lương. Cái giá là có thể bỏ nhầm vài tin có khoảng thật sự rộng.",
    ],
  },
  {
    section: "Phần 1 · Dữ liệu",
    layout: "big",
    title: "Phát hiện lớn nhất: 2.400 tin là tin giả do máy sinh ra",
    big: { value: "2.400", caption: "tin giả: cùng kiểu đường link, đúng 800 tin mỗi trang, kỹ năng ngẫu nhiên" },
    note: "Ví dụ: tin “Android Developer” lại đòi Swift và React – hai thứ không liên quan",
    script: [
      "Bây giờ là phát hiện quan trọng nhất của cả dự án, và nó đến muộn nhất.",
      "Ngay từ đầu nhóm đã thấy một điều lạ: ở ba trang TopCV, VietnamWorks, CareerViet, mỗi năm từ 2018 đến 2025 đều có số tin gần như bằng nhau. Thị trường thật không bao giờ đều như vậy. Lúc đầu nhóm chỉ nghĩ cột ngày đăng bị hỏng, nên dùng năm thu thập thay thế, rồi làm tiếp.",
      "Đến cuối dự án, khi kiểm tra chất lượng nhãn, nhóm đào sâu hơn và thấy toàn bộ những tin đó có chung dấu hiệu. Đường link đều có dạng \"hist\" kèm một dãy số. Mỗi trang có đúng 800 tin, không hơn không kém. Danh sách kỹ năng thì ngẫu nhiên: một tin tuyển lập trình viên Android lại đòi Swift và React, là những thứ không liên quan. Và không tin nào có mô tả công việc. Kết luận: đây là 2.400 tin do máy sinh ra, không phải tin tuyển dụng thật. Chúng chiếm tới 54% số tin có lương.",
    ],
  },
  {
    section: "Phần 1 · Dữ liệu",
    layout: "compare",
    title: "Bỏ tin giả: con số xấu đi, nhưng trung thực hơn",
    compare: {
      left: { head: "Có lẫn tin giả", lines: ["3.809 tin", "Sai số điển hình 16,5%", "→ trông đẹp hơn thực tế"] },
      right: { head: "Chỉ tin thật", lines: ["1.735 tin", "Mô hình cũ sai 18,0%", "Mô hình mới sai 16,9%"] },
    },
    note: "“Sai số điển hình” ở đây là trung vị sai số: một nửa số dự đoán lệch ít hơn con số này",
    script: [
      "Tại sao tin giả lại nguy hiểm? Vì tin giả dễ đoán hơn tin thật. Khi tập kiểm tra có lẫn tin giả, mô hình cũ trông như chỉ sai khoảng 16,5%. Nhưng nếu chỉ chấm trên tin thật, nó sai 18%. Nghĩa là con số đẹp trước đây là đẹp giả.",
      "Giống như học sinh ôn thi bằng bộ đề do máy bịa ra: điểm luyện tập rất cao, nhưng không cho biết làm đề thật thế nào.",
      "Nhóm cân nhắc ba cách: giữ tin giả và chỉ sửa cột ngày, giữ nhưng đánh dấu, hoặc bỏ hẳn. Nhóm chọn bỏ hẳn, vì mục tiêu là đoán lương của tin thật. Cái giá rất lớn: mất hơn một nửa dữ liệu, chỉ còn 1.735 tin thật, và tập dùng để chấm điểm chỉ còn 288 tin. Sau đó nhóm huấn luyện lại trên tin thật, thêm vài thông tin mới như trang đăng tin và loại công ty, và mô hình mới sai 16,4% trên tin thật.",
      "Em nghĩ đây là bài học lớn nhất của dự án: nhiều dữ liệu chỉ có giá trị khi dữ liệu là thật.",
    ],
  },
  {
    section: "Phần 1 · Dữ liệu",
    layout: "big",
    title: "Kiểm tra lại máy gán nhãn trên 208 tin",
    big: { value: "100%", caption: "lương đọc đúng · vai trò đúng 95% → 99,5% sau khi sửa luật · lần kiểm tra thứ hai: 67 tin, sai 0–3%" },
    note: "Mẫu do AI duyệt, cần người duyệt lại trước khi dùng làm số chính thức",
    script: [
      "Toàn bộ nhãn, tức lương, vị trí, cấp bậc, kỹ năng, đều do các quy tắc tự động gán. Câu hỏi là: các quy tắc đó sai bao nhiêu? Nếu sai nhiều, máy học từ nhãn sai mà không ai biết.",
      "Duyệt lại cả 1.735 tin thì quá lâu. Nhóm làm như kiểm tra chất lượng trong nhà máy: lấy một mẫu đại diện 208 tin, rải đều các trang và các vị trí, rồi so từng nhãn tự động với tin gốc.",
      "Kết quả: lương và kinh nghiệm đọc đúng 100%. Vị trí đúng 95%, cấp bậc gần 95%. Các lỗi tìm được rất cụ thể: \"MERN stack\" bị xếp nhầm nhóm, chữ \"Senior\" trong tên vị trí bị trang web ghi đè thành \"Trưởng nhóm\", \"API Testing\" bị hiểu nhầm thành kỹ năng REST API. Nhóm sửa luật, và trên cùng mẫu đó vị trí đúng 99,5%, cấp bậc 100%.",
      "Em xin nói thẳng hai lưu ý. Mẫu này do AI duyệt theo yêu cầu của nhóm, chưa có người duyệt lại. Và con số sau khi sửa được đo trên chính mẫu đã dùng để tìm lỗi, nên có thể hơi lạc quan. Dù vậy, kết luận chính đứng vững: máy gán nhãn không phải là nguyên nhân chính khiến mô hình sai.",
      "Sau đó nhóm kiểm tra thêm một lần trên 67 tin mới chọn ngẫu nhiên. Lương và kinh nghiệm không sai tin nào; vai trò sai 3%, cấp bậc 1,5%, kỹ năng 2%. Ba lỗi lặp lại, ví dụ chữ \"Node.js\" bị hiểu nhầm là kỹ năng JavaScript, được sửa thẳng trong luật; hai lỗi chỉ gặp một lần được ghi vào sổ nhãn đã duyệt.",
    ],
  },
  {
    section: "Phần 1 · Dữ liệu",
    title: "Chia “đề thi” theo công ty, không chia ngẫu nhiên",
    points: [
      "Một công ty đăng hàng chục tin gần giống nhau",
      "Chia ngẫu nhiên = cho ôn đúng đề sẽ thi → điểm cao giả",
      "Mỗi công ty chỉ nằm ở một phần: 1.169 tin để học · 278 để chọn · 288 để thi",
    ],
    fig: "figures/split.png",
    script: [
      "Để biết mô hình đoán tốt hay không, phải giữ lại một phần dữ liệu làm \"đề thi\" mà mô hình chưa từng thấy.",
      "Cách thông thường là chia ngẫu nhiên. Nhưng với tin tuyển dụng có một cái bẫy: một công ty thường đăng hàng chục tin gần giống nhau, cùng khung lương. Nếu chia ngẫu nhiên, tin của công ty A nằm trong phần học, tin gần giống hệt nằm trong đề thi. Mô hình chỉ cần nhớ \"công ty A trả 25 triệu\" là đoán đúng. Giống như cho học sinh ôn đúng đề sẽ thi: điểm cao, nhưng không biết làm đề mới.",
      "Nên nhóm chia theo công ty: mọi tin của một công ty nằm trọn trong một phần. Phần học có 1.169 tin, phần dùng để chọn mô hình có 278 tin, và phần thi cuối cùng có 288 tin của 121 công ty mà mô hình chưa từng gặp. Đúng với câu hỏi thật của người dùng: công ty mới mà tôi ứng tuyển sẽ trả bao nhiêu.",
      "Thêm một chi tiết: phần thi chỉ được mở đúng một lần, sau khi đã chọn xong mô hình. Nếu nhìn điểm thi rồi quay lại sửa, thì đề thi không còn là đề mới nữa.",
    ],
  },

  // ───────────────────────── PHẦN 2: THỊ TRƯỜNG
  { section: "Phần 2 · Thị trường", layout: "section", title: "Phần 2\nThị trường đang nói gì", script: ["Sang phần hai: sau khi làm sạch, thị trường đang nói gì. Tất cả biểu đồ vẽ bằng Matplotlib và Seaborn trên 1.735 tin thật."] },
  {
    section: "Phần 2 · Thị trường",
    layout: "big",
    title: "Mức lương chào tuyển phổ biến: 25 triệu/tháng",
    big: { value: "25 triệu", caption: "một nửa số tin trả thấp hơn, một nửa trả cao hơn" },
    fig: "figures/distribution.png",
    script: [
      "Mức lương chào tuyển ở giữa là 25 triệu mỗi tháng: một nửa số tin trả thấp hơn, một nửa trả cao hơn. Con số này gọi là trung vị.",
      "Tại sao em dùng trung vị mà không dùng trung bình? Ví dụ một phòng có 9 người lương 20 triệu và một giám đốc lương 200 triệu. Trung bình là 38 triệu, nhưng không ai trong 9 người kia nhận gần 38 triệu. Trung vị là 20 triệu, đúng với \"người bình thường\" hơn. Biểu đồ cũng cho thấy phần lớn tin nằm trong khoảng 15 đến 35 triệu, nhưng có một cái đuôi dài lên tới hơn 100 triệu ở các vị trí quản lý.",
      "Em cũng xin lưu ý: đây là lương ghi trên tin tuyển dụng, chưa rõ là trước hay sau thuế, và không phải lương thực nhận.",
    ],
  },
  {
    section: "Phần 2 · Thị trường",
    title: "Kinh nghiệm là thứ quyết định lương nhiều nhất",
    points: ["Dưới 1 năm: 13,5 triệu", "3 năm: 28 triệu", "5–7 năm: 48 triệu – nhảy vọt khi lên Senior"],
    fig: "figures/experience.png",
    script: [
      "Yếu tố ảnh hưởng mạnh nhất là số năm kinh nghiệm. Người dưới 1 năm có mức giữa khoảng 13,5 triệu, 3 năm khoảng 28 triệu, và 5 đến 7 năm lên tới 48 triệu.",
      "Bước nhảy lớn nhất nằm giữa năm thứ 4 và năm thứ 5, đúng lúc chuyển từ Middle lên Senior. Ngoài đời điều này rất dễ hiểu: lên Senior không chỉ là thêm một năm, mà là đổi vai trò, bắt đầu chịu trách nhiệm thiết kế và kèm người khác.",
      "Về mặt kỹ thuật, nhóm đo độ liên hệ bằng hệ số Spearman, được 0,70 trên thang từ 0 đến 1, tức là liên hệ mạnh. Spearman chỉ hỏi một câu đơn giản: người nhiều kinh nghiệm hơn có thường được trả cao hơn không, mà không đòi hỏi quan hệ phải là đường thẳng.",
    ],
  },
  {
    section: "Phần 2 · Thị trường",
    layout: "compare",
    title: "Kỹ năng phổ biến nhất chưa chắc là kỹ năng lương cao nhất",
    compare: {
      left: { head: "Được tuyển nhiều nhất", lines: ["Java · 179 tin", "React · 154 tin", "SQL · 129 tin"] },
      right: { head: "Lương cao nhất", lines: ["AWS · 36 triệu", "LLM / AI tạo sinh · 35 triệu", "Next.js · 34 triệu"] },
    },
    note: "Kỹ năng phổ biến giúp dễ tìm việc; kỹ năng hiếm gắn với lương cao",
    script: [
      "Đây là phát hiện em thấy thú vị nhất. Nếu đếm số tin nhắc tới, đứng đầu là Java, React và SQL. Nhưng nếu xếp theo mức lương, đứng đầu lại là AWS, tức điện toán đám mây của Amazon, rồi đến LLM, tức AI tạo sinh kiểu ChatGPT, rồi Next.js.",
      "Hiểu theo đời thường: kỹ năng phổ biến là thứ giúp bạn dễ tìm việc; kỹ năng hiếm, gắn với AI và đám mây, là thứ gắn với lương cao. Còn những công nghệ như PHP, MySQL có mức giữa chỉ khoảng 20 triệu.",
      "Em xin lưu ý: đây mới là mô tả. Có thể tin đòi AWS là tin tuyển người nhiều kinh nghiệm, nên lương cao là nhờ kinh nghiệm chứ không phải nhờ AWS. Phần mô hình sẽ tách được hai yếu tố này.",
    ],
  },
  {
    section: "Phần 2 · Thị trường",
    title: "Lương khác nhau rõ theo vị trí",
    points: ["Data Engineer, Tech Lead, quản lý IT: khoảng 40 triệu", "Lập trình viên Backend, Frontend, Mobile: 25 triệu", "Tester, hỗ trợ IT: 14–20 triệu"],
    fig: "figures/roles.png",
    script: [
      "Theo vị trí, cao nhất là kỹ sư dữ liệu, trưởng nhóm kỹ thuật và quản lý IT, khoảng 40 triệu. Nhưng em xin lưu ý là kỹ sư dữ liệu chỉ có 26 tin và quản lý IT chỉ 13 tin, nên con số này chưa thật vững.",
      "Lập trình viên phổ thông như Backend, Frontend, Mobile ở mức 25 triệu. Thấp nhất là kiểm thử và hỗ trợ IT, khoảng 14 đến 20 triệu.",
    ],
  },
  {
    section: "Phần 2 · Thị trường",
    title: "Hà Nội hay TP.HCM trả cao hơn? Dữ liệu chưa cho phép kết luận",
    points: ["80% số tin có lương ở Hà Nội", "Công ty ở TP.HCM hay ghi “Thương lượng”", "Cùng một nghề, hai thành phố chỉ chênh 0–2 triệu"],
    script: [
      "Một câu hỏi rất hay gặp: Hà Nội hay TP.HCM trả cao hơn? Em xin trả lời thật: dữ liệu này chưa đủ để kết luận.",
      "80% số tin có lương nằm ở Hà Nội. Lý do không phải TP.HCM ít việc, mà là các công ty ở TP.HCM có thói quen ghi \"Thương lượng\", nên rất ít tin có con số. Đây là đặc điểm của thị trường, không sửa được bằng kỹ thuật, chỉ có thể nói rõ.",
      "Với những nghề có nhiều tin như Backend hay kiểm thử, hai thành phố chỉ chênh 0 đến 2 triệu. Những chênh lệch lớn chỉ xuất hiện ở các nghề có vài tin, nên không đáng tin.",
    ],
  },

  // ───────────────────────── PHẦN 3: MÔ HÌNH
  { section: "Phần 3 · Mô hình", layout: "section", title: "Phần 3\nDạy máy đoán lương", script: ["Sang phần ba: dạy máy đoán lương. Em sẽ không nói về code, mà so mỗi mô hình với cách một người làm nhân sự định lương."] },
  {
    section: "Phần 3 · Mô hình",
    title: "Bốn cách đoán lương – như bốn người làm nhân sự",
    points: [
      "Đoán bừa: ai hỏi cũng trả lời “25 triệu”",
      "Bảng giá cộng dồn: Backend +2, mỗi năm +3, biết AWS +1 (Ridge)",
      "Hỏi 300 người rồi lấy trung bình (Random Forest)",
      "Hội đồng sửa sai nối tiếp, mỗi người sửa chỗ người trước sai (Gradient Boosting)",
    ],
    script: [
      "Nhóm thử bốn cách đoán lương.",
      "Cách thứ nhất là đoán bừa: ai hỏi cũng trả lời 25 triệu. Nghe buồn cười, nhưng nó là thước đo tối thiểu. Một mô hình chỉ có giá trị nếu tốt hơn rõ rệt so với cách trả lời lười biếng này.",
      "Cách thứ hai, tên kỹ thuật là Ridge, giống một chuyên viên nhân sự có sẵn bảng giá: làm Backend cộng 2 triệu, mỗi năm kinh nghiệm cộng 3 triệu, biết AWS cộng 1 triệu, rồi cộng lại. Dễ giải thích, ổn định. Nhưng nó không hiểu \"tùy hoàn cảnh\": ngoài đời, AWS đáng giá với kỹ sư hạ tầng hơn hẳn với người kiểm thử, mà bảng giá chỉ có một con số cho AWS.",
      "Cách thứ ba, tên là Random Forest, giống như hỏi ý kiến 300 chuyên viên, mỗi người chỉ được xem một phần hồ sơ và chỉ từng gặp một phần thị trường, rồi lấy trung bình. Ý tưởng là sai lầm của từng người sẽ bù trừ nhau. Ngoài đời không công ty nào làm vậy, cũng không ai tự có 300 góc nhìn độc lập cùng lúc, nhưng máy thì làm được.",
      "Cách thứ tư, tên là Gradient Boosting, giống một hội đồng làm việc nối tiếp: người đầu đưa ra mức sơ bộ, người thứ hai chỉ tập trung sửa những hồ sơ người đầu đánh giá sai, người thứ ba sửa tiếp phần còn sai. Mỗi người chỉ sửa một bước nhỏ nên không vội học vẹt theo vài trường hợp lạ. Cách này học được những quy luật tinh tế như \"AWS có giá trị với kỹ sư hạ tầng nhưng ít giá trị với người kiểm thử\".",
      "Nhóm không dùng mạng nơ-ron, tức kiểu AI học sâu, vì với khoảng một nghìn tin dạng bảng thì các cách dựa trên cây quyết định như trên thường tốt hơn, nhanh hơn và dễ giải thích hơn.",
    ],
  },
  {
    section: "Phần 3 · Mô hình",
    layout: "compare",
    title: "Luật đời thường: biết thêm kỹ năng thì lương không thể giảm",
    compare: {
      left: { head: "Trước khi sửa", lines: ["Backend, 5 năm: 47,7 triệu", "Thêm Java: 42,3 triệu ↓", "→ lời khuyên vô lý"] },
      right: { head: "Sau khi thêm luật", lines: ["Thêm Java: không giảm", "Thêm Java, Docker, AWS: tăng ↑", "→ lời khuyên luôn hợp lý"] },
    },
    note: "Áp dụng cho cả kinh nghiệm: làm thêm năm nữa thì lương dự đoán không giảm",
    script: [
      "Có một lỗi nhóm phát hiện khi chạy thử ứng dụng. Với hồ sơ lập trình viên Backend 5 năm kinh nghiệm, mô hình đoán 47,7 triệu. Thêm đúng một kỹ năng là Java, lương dự đoán lại giảm còn 42,3 triệu. Một công cụ tư vấn mà nói \"học Java thì mất 5 triệu\" thì rõ ràng là sai.",
      "Điều thú vị là máy không hề bị lỗi lập trình. Nó học đúng những gì dữ liệu nói. Cột kỹ năng ghi những gì tin tuyển dụng yêu cầu, không phải những gì ứng viên có. Mà ngoài đời, tin liệt kê 7, 8 kỹ năng thường là tin tuyển người mới hoặc tuyển hàng loạt, viết dài cho đủ, còn tin tuyển Senior lương cao thường chỉ ghi vài kỹ năng cốt lõi. Máy học được \"tin nhiều kỹ năng thì lương thấp\". Đúng để đoán lương của một tin tuyển dụng, nhưng sai hoàn toàn khi trả lời câu hỏi \"tôi học thêm kỹ năng thì sao\".",
      "Nhóm thêm một luật cứng vào mô hình: biết thêm kỹ năng thì lương dự đoán không được giảm. Luật tương tự đã có từ trước cho kinh nghiệm: làm thêm một năm thì lương dự đoán không được giảm. Mức tăng của từng kỹ năng vẫn để dữ liệu quyết định, nhóm không bịa ra mức cộng nào.",
      "Cái giá là mô hình sai nhiều hơn một chút, vì nó không còn được dùng cái mẹo \"đếm số kỹ năng\". Nhóm chấp nhận, vì một công cụ tư vấn sai thêm một chút nhưng luôn khuyên hợp lý thì hữu ích hơn một công cụ chính xác hơn chút ít mà khuyên điều vô lý.",
    ],
  },
  {
    section: "Phần 3 · Mô hình",
    layout: "big",
    title: "Mô hình tốt nhất sai trung bình khoảng 6,5 triệu mỗi dự đoán",
    big: { value: "≈ 6,5 triệu", caption: "sai trung bình mỗi tin · đoán bừa sai 11,3 triệu" },
    note: "Một nửa số dự đoán lệch không quá khoảng 16,9% so với lương thật",
    script: [
      "Kết quả trên 288 tin thi, của những công ty mô hình chưa từng gặp. Cách hội đồng sửa sai nối tiếp, tức Gradient Boosting, tốt nhất: trung bình mỗi dự đoán lệch khoảng 6,5 triệu. Trong khi đoán bừa \"ai cũng 25 triệu\" lệch 11,3 triệu. Tức là sai số giảm khoảng 42%.",
      "Nói theo phần trăm thì dễ hình dung hơn: một nửa số dự đoán lệch không quá khoảng 16,9% so với lương thật. Với mức lương 25 triệu, 16,9% tương ứng khoảng 4,2 triệu.",
      "Thuật ngữ chuyên môn: con số 6,5 triệu gọi là MAE, sai số tuyệt đối trung bình. Nhóm chọn MAE làm tiêu chí chọn mô hình từ trước khi xem kết quả, vì nó có đơn vị là tiền và trả lời đúng câu người dùng quan tâm: \"đoán sai trung bình bao nhiêu tiền\".",
    ],
  },
  {
    section: "Phần 3 · Mô hình",
    title: "Mô hình đoán tốt người làm nghề phổ thông, kém ở vị trí quản lý",
    points: ["Kiểm thử, Frontend, hỗ trợ IT: lệch 3–5 triệu", "Trưởng nhóm kỹ thuật: lệch hơn 20 triệu", "Lương quản lý phụ thuộc quy mô công ty – dữ liệu không có"],
    fig: "figures/error_role.png",
    script: [
      "Một con số trung bình có thể che giấu nhiều thứ, nên nhóm xem mô hình sai ở đâu. Với các nghề có khung lương hẹp như kiểm thử, Frontend, hỗ trợ IT, mô hình chỉ lệch khoảng 3 đến 5 triệu. Với trưởng nhóm kỹ thuật thì lệch hơn 20 triệu.",
      "Em cho rằng đây không hẳn là lỗi của mô hình. Ngoài đời, lương trưởng nhóm ở một công ty khởi nghiệp 20 người khác rất xa ở một tập đoàn 5.000 người, dù cùng chức danh, cùng số năm. Thông tin quy mô công ty không có trong tin tuyển dụng, nên không mô hình nào đoán đúng được.",
    ],
  },
  {
    section: "Phần 3 · Mô hình",
    title: "Học thêm gì thì lương dự đoán tăng nhiều nhất?",
    points: ["AI tạo sinh (LLM): gần +8 triệu", "AWS: +3,4 triệu · Next.js, React Native: +2,4 triệu", "JavaScript, Java: gần 0 – là điều kiện để có việc"],
    fig: "figures/uplift.png",
    script: [
      "Để biết học gì thì lương tăng, nhóm làm phép thử \"nếu như\": lấy một hồ sơ, giữ nguyên vị trí, kinh nghiệm, nơi làm việc, chỉ thêm đúng một kỹ năng, rồi xem lương dự đoán tăng bao nhiêu.",
      "Đứng đầu là AI tạo sinh, cộng gần 8 triệu, rồi AWS hơn 3 triệu, Next.js và React Native khoảng 2,4 triệu, Kafka hơn 2 triệu. Ngược lại JavaScript và Java gần như không cộng thêm: đây là kỹ năng nền tảng mà tin nào cũng đòi, nên biết chúng là điều kiện để có việc, không phải lý do để được trả thêm.",
      "Em xin nhấn mạnh: đây là quan hệ học từ tin tuyển dụng, không phải lời hứa. Không có gì đảm bảo học xong AI tạo sinh thì được tăng gần 8 triệu. Có thể công ty đòi AI tạo sinh là công ty lớn, và chính quy mô công ty mới là lý do trả cao.",
    ],
  },

  // ───────────────────────── PHẦN 4: KIỂM ĐỊNH
  { section: "Phần 4 · Có tin được không?", layout: "section", title: "Phần 4\nMô hình có đáng tin không?", script: ["Phần bốn là phần em cho là quan trọng nhất: mô hình có đáng tin không. Một con số sai trung bình chưa trả lời được câu đó."] },
  {
    section: "Phần 4 · Có tin được không?",
    layout: "big",
    title: "Nói “80% khả năng” thì có đúng 80% không?",
    big: { value: "83%", caption: "lương thật nằm trong khoảng mà mô hình nói là “80%”" },
    fig: "figures/reliability.png",
    script: [
      "Ứng dụng không chỉ đưa một con số mà đưa một khoảng, ví dụ \"lương thường nằm trong khoảng 13 đến 30 triệu, với 80% khả năng\". Câu hỏi là: khoảng đó có thật sự đúng 80% không?",
      "Ví dụ đời thường là dự báo thời tiết. Nếu đài nói \"80% khả năng mưa\" cho 100 ngày, thì một đài tốt phải có khoảng 80 ngày thật sự mưa. Nếu chỉ 50 ngày mưa thì đài đó tự tin quá mức. Phép kiểm tra này trong chuyên môn gọi là hiệu chuẩn.",
      "Kết quả: khoảng mà mô hình nói là 80% thực tế chứa 83% lương thật. Tức là khoảng hơi rộng hơn cần thiết, nói cách khác là thận trọng, người dùng ít khi bị bất ngờ. Riêng với lương rất cao thì khoảng chỉ đúng 72%, mô hình tự tin hơn mức nên có.",
    ],
  },
  {
    section: "Phần 4 · Có tin được không?",
    title: "Thi lại 1.000 lần với đề khác: thắng 83–91% số lần – chưa đủ chắc",
    points: ["Đổi ngẫu nhiên các công ty trong đề thi, chấm lại 1.000 lần", "Gradient Boosting thắng hai cách kia 83–91% số lần", "Muốn khẳng định chắc chắn cần thêm tin thật"],
    fig: "figures/bootstrap.png",
    script: [
      "Câu hỏi thứ hai: Gradient Boosting thắng, nhưng có phải nhờ may mắn với 121 công ty cụ thể trong đề thi không?",
      "Cách công bằng nhất là cho thi lại bằng nhiều đề khác nhau. Không có thêm dữ liệu, nhóm giả lập bằng cách rút ngẫu nhiên lại các công ty từ chính đề thi, có công ty được rút nhiều lần, có công ty không được rút, tạo ra 1.000 đề mới rồi chấm lại. Kỹ thuật này gọi là bootstrap. Nhóm rút theo công ty, không rút theo từng tin, vì các tin cùng công ty giống nhau.",
      "Kết quả: Gradient Boosting thắng hai cách kia trong khoảng 83 đến 91% số đề. Nghe thì nhiều, nhưng theo chuẩn thống kê thì chưa đủ để khẳng định chắc chắn. Trước khi bỏ tin giả, con số này là 100%, nhưng đó là trên dữ liệu đẹp giả. Em xin nói thật: với 288 tin thi, chưa đủ bằng chứng nó tốt hơn hẳn. Nhóm vẫn giữ nó vì nó thắng theo tiêu chí đã chốt từ trước, và nó hỗ trợ luật \"thêm kỹ năng không giảm lương\" một cách tự nhiên. Còn so với đoán bừa thì nó thắng 100% số lần.",
    ],
  },
  {
    section: "Phần 4 · Có tin được không?",
    title: "Mô hình có thiên vị ai không?",
    points: ["Hà Nội, TP.HCM: không có dấu hiệu thiên vị", "Người mới (Junior): đoán cao khoảng 7% → nên trừ hao", "Giới tính: dữ liệu không có, nên không đo được"],
    fig: "figures/fair_level.png",
    script: [
      "Câu hỏi thứ ba là công bằng. Ví dụ đời thường: một chiếc cân lệch 1 ký với tất cả mọi người thì vẫn công bằng; nhưng nếu nó chỉ lệch với người thấp, còn đúng với người cao, thì đó là thiên vị. Nhóm kiểm tra xem mô hình có đoán lệch có hệ thống cho nhóm nào không.",
      "Theo thành phố, Hà Nội và TP.HCM đều lệch vài phần trăm và không có ý nghĩa thống kê, nên không có dấu hiệu thiên vị. Theo cấp bậc, có một phát hiện rõ: người Junior, tức đi làm 1 đến 2 năm, bị đoán cao hơn thực tế khoảng 7%. Ý nghĩa thực tế: nếu bạn mới đi làm dùng con số này để thương lượng lương thì nên trừ hao một chút.",
      "Về giới tính, em xin nói thẳng: không đo được. Dữ liệu là tin tuyển dụng, không có giới tính của người được tuyển. Mô hình cũng không dùng giới tính, nên nó không thể trả lương khác nhau cho nam và nữ cùng hồ sơ. Nhưng nói \"mô hình công bằng giới\" thì không trung thực, vì không có dữ liệu để kiểm. Điều kiểm tra được là chính các tin: có 7 tin ghi điều kiện giới tính, ví dụ \"Tester game chỉ tuyển nữ\". Đây là dấu hiệu phân biệt đối xử theo Bộ luật Lao động, và một hệ thống thật nên cảnh báo các tin như vậy.",
    ],
  },
  {
    section: "Phần 4 · Có tin được không?",
    layout: "compare",
    title: "So với chuẩn của Glassdoor, LinkedIn: chưa đạt",
    compare: {
      left: { head: "Chuẩn đặt ra", lines: ["Một nửa dự đoán lệch ≤ 15%", "≥ 65% dự đoán lệch ≤ 20%", "Khoảng 80% đúng 75–85%"] },
      right: { head: "Mô hình hiện tại", lines: ["16,9% – chưa đạt", "55% – chưa đạt", "83% – đạt (gần sát)"] },
    },
    note: "Đạt với Backend, Kiểm thử, Mobile, Fullstack và cấp Junior, Middle, Senior; trượt ở cấp Lead",
    script: [
      "Câu hỏi cuối cùng và thực tế nhất: mô hình đã đủ tốt để đưa cho người dùng thật chưa?",
      "Thay vì tự đặt ra một ngưỡng, nhóm dùng cách các sản phẩm dự đoán lương thật đang làm. Glassdoor công bố hai con số: một nửa dự đoán của họ lệch dưới 10%, và 75% dự đoán lệch không quá 20%. LinkedIn hiển thị một khoảng lương thay vì một con số. Vì Glassdoor có lương thực nhận và thông tin công ty, còn nhóm chỉ có lương trên tin tuyển dụng, nên nhóm đặt chuẩn nới hơn: một nửa dự đoán lệch không quá 15%, ít nhất 65% dự đoán lệch không quá 20%, và khoảng 80% phải đúng trong khoảng 75 đến 85%.",
      "Kết quả: mô hình chưa đạt. Một nửa dự đoán lệch 16,9%, chỉ 55% dự đoán lệch không quá 20%. Riêng khoảng 80% thì đúng 83%, nằm trong chuẩn. Theo nhóm, bốn nghề đông tin là Backend, Kiểm thử, Mobile, Fullstack và ba cấp Junior, Middle, Senior đạt; cấp trưởng nhóm thì trượt rõ. Mười tám nghề còn lại có quá ít tin thi nên chưa chấm được.",
      "Em nghĩ nói thật kết quả này quan trọng hơn là trình bày một con số đẹp. Và nhóm đã kiểm tra: nguyên nhân chính không phải do máy gán nhãn sai, mà do quá ít tin thật. Cách hiệu quả nhất để đạt chuẩn là có thêm dữ liệu thật.",
    ],
  },
  {
    section: "Phần 4 · Có tin được không?",
    layout: "big",
    title: "So với báo cáo lương thật: 8/10 nghề lệch không quá 15%",
    big: { value: "8/10", caption: "nghề có lương dự đoán lệch ≤ 15% so với báo cáo lương TopDev" },
    note: "Hai nghề còn lệch: Frontend (đoán thấp hơn) và Mobile (đoán cao hơn)",
    script: [
      "Lương trên tin tuyển dụng chưa chắc là lương người đi làm thật sự nhận. Vì vậy nhóm đối chiếu thêm với báo cáo lương do TopDev và ITviec công bố, tức số liệu khảo sát người đang đi làm.",
      "Để so được, ứng dụng nhân dự đoán với một hệ số, gọi là hiệu chỉnh, để quy lương trên tin về lương gross thị trường gần đúng. Ví dụ với Backend cấp Junior ở Hà Nội, hệ số là khoảng 1,2.",
      "Kết quả: ở 8 trên 10 nghề, lương dự đoán lệch không quá 15% so với báo cáo, đạt mục tiêu nhóm đặt ra là ít nhất 8 nghề. Hai nghề còn lệch là Frontend, đoán thấp hơn khoảng 18%, và Mobile, đoán cao hơn khoảng 17%.",
      "Em xin nói thật một giới hạn: báo cáo lương cũng được dùng để tính hệ số, nên con số 8/10 cho biết hệ thống nhất quán với báo cáo, chưa phải bằng chứng độc lập hoàn toàn. Muốn kiểm tra độc lập cần lương thật của người đi làm; đây là việc nhóm sẽ làm tiếp.",
    ],
  },
  {
    section: "Phần 4 · Có tin được không?",
    title: "Vì vậy ứng dụng nói thật với người dùng",
    points: ["Ghi rõ: “Kết quả mang tính tham khảo”", "Hiện khoảng lương trước, con số sau", "Ít dữ liệu (dưới 20 tin cùng nghề, cùng cấp) → chỉ hiện khoảng"],
    script: [
      "Từ kết quả đó, ứng dụng làm ba việc.",
      "Thứ nhất, ngay đầu trang ghi rõ \"Kết quả mang tính tham khảo, mô hình chưa đạt chuẩn độ chính xác\".",
      "Thứ hai, ứng dụng hiện khoảng lương trước, con số sau. Giống dự báo thời tiết nói \"26 đến 32 độ\" thay vì \"29,3 độ\": người nghe hiểu ngay mức độ chắc chắn. Con số chỉ được gọi là \"mức điển hình\" và ghi kèm có bao nhiêu tin cùng nghề, cùng cấp làm căn cứ.",
      "Thứ ba, nếu hồ sơ thuộc nhóm có dưới 20 tin cùng nghề, cùng cấp bậc, ứng dụng không đưa con số nào cả, chỉ đưa một khoảng rộng hơn kèm lý do. Một người tư vấn trung thực sẽ nói \"với vị trí này tôi chỉ biết lương thường trong khoảng 24 đến 60 triệu\", thay vì bịa ra một con số. Ngưỡng 20 tin là theo cách LinkedIn làm.",
    ],
  },

  // ───────────────────────── PHẦN 5: ỨNG DỤNG
  { section: "Phần 5 · Ứng dụng", layout: "section", title: "Phần 5\nỨng dụng tư vấn", script: ["Phần năm là ứng dụng. Em xin demo trực tiếp."] },
  {
    section: "Phần 5 · Ứng dụng",
    title: "Demo: lập trình viên Backend, Hà Nội, 3 năm, biết Java, Spring Boot, SQL",
    points: ["Lương gross gần đúng 21–31 triệu, mức điển hình 26 triệu", "Cao hơn 36% số tin Backend · Nên học: Kafka (+5,7), Python (+5,5)", "Lên Senior (5 năm): khoảng 34 triệu"],
    fig: "figures/ui-advisor-crop.png",
    script: [
      "Em nhập hồ sơ: lập trình viên Backend ở Hà Nội, 3 năm kinh nghiệm, biết Java, Spring Boot và SQL, rồi bấm \"Dự đoán và tư vấn\".",
      "Ứng dụng trả về khoảng lương 21 đến 31 triệu, mức điển hình khoảng 26 triệu, dựa trên 59 tin cùng nghề, cùng cấp. Đây là lương gross, tức trước thuế và bảo hiểm, được quy đổi gần đúng từ lương ghi trên tin tuyển dụng theo báo cáo lương của TopDev và ITviec. Khoảng này chứa một nửa số tin tương tự.",
      "Ô \"Vị trí so với vai trò\" ghi \"Cao hơn 36% tin\": mức dự đoán cho hồ sơ này cao hơn 36% số tin tuyển dụng Backend và thấp hơn 64% còn lại. Trong thống kê, con số này gọi là phân vị, viết tắt P36; ứng dụng viết bằng chữ cho dễ hiểu và có chú thích khi rê chuột.",
      "Phần gợi ý: nên học Kafka, cộng khoảng 5,7 triệu; Python 5,5 triệu; Golang 3,9 triệu; rồi Kubernetes và Microservices. Mỗi gợi ý kèm tỉ lệ tin cùng nghề có yêu cầu kỹ năng đó.",
      "Phần lộ trình cho thấy lương tăng chậm khi còn ở cấp Middle, rồi nhảy lên khoảng 34 triệu khi đủ 5 năm và lên Senior, đúng như biểu đồ kinh nghiệm em trình bày ở phần hai.",
      "Một điểm kỹ thuật: ứng dụng không huấn luyện lại mỗi lần bấm, mà dùng mô hình đã lưu sẵn. Như vậy cùng một hồ sơ thì hôm nay và ngày mai ra cùng kết quả, phản hồi dưới một giây, và mô hình người dùng đang dùng chính là mô hình đã được chấm điểm.",
    ],
  },
  {
    section: "Phần 5 · Ứng dụng",
    title: "Khi ít dữ liệu: chỉ hiện khoảng, kèm lý do",
    points: ["Data Engineer cấp Middle: chỉ có 7 tin", "→ chỉ hiện khoảng 24–60 triệu, cảnh báo “Ít dữ liệu”", "Không hiện mức tăng lương của từng kỹ năng"],
    fig: "figures/ui-advisor-lowdata-crop.png",
    script: [
      "Bây giờ em đổi sang hồ sơ kỹ sư dữ liệu 3 năm kinh nghiệm. Nhóm nghề này ở cấp Middle chỉ có 7 tin có lương.",
      "Ứng dụng không đưa con số nào, chỉ đưa khoảng 24 đến 60 triệu, kèm cảnh báo màu vàng \"Ít dữ liệu\" và giải thích bằng lời thường. Ai muốn biết chi tiết kỹ thuật có thể bấm \"Vì sao?\". Các kỹ năng vẫn được gợi ý, nhưng không kèm con số tăng lương, vì với 7 tin thì con số đó không đáng tin.",
    ],
  },
  {
    section: "Phần 5 · Ứng dụng",
    title: "Thêm dữ liệu mới bằng một lệnh, quay lại bản cũ khi cần",
    points: ["Nhập file tin mới → máy tự gắn nhãn, tạo dữ liệu, huấn luyện, chấm điểm", "Mô hình mới chỉ được dùng khi tốt hơn bản cũ; có thể quay lại bản trước", "Tin máy không hiểu được đưa vào danh sách chờ người duyệt"],
    script: [
      "Một mô hình chỉ tốt lên khi có thêm dữ liệu thật. Vì vậy nhóm làm sẵn một lệnh duy nhất: người quản trị đưa vào một file tin tuyển dụng mới, hệ thống tự gắn nhãn, tạo lại bộ dữ liệu, huấn luyện, chấm điểm.",
      "Mô hình mới chỉ được đưa vào dùng nếu qua \"cổng kiểm tra\": đạt chuẩn, hoặc tốt hơn mô hình đang chạy. Mỗi lần huấn luyện được lưu thành một phiên bản riêng; nếu có sự cố, một lệnh là quay lại phiên bản trước. Trên ứng dụng có một dòng nhỏ cho biết đang dùng phiên bản nào, cập nhật ngày nào, học từ bao nhiêu tin.",
      "Tin nào máy không hiểu, ví dụ lương ghi \"thỏa thuận\" hay chức danh lạ, không bị bỏ mất mà được đưa vào danh sách chờ người duyệt. Quyết định của người duyệt được ghi lại và áp dụng ở lần tạo dữ liệu sau.",
    ],
  },
  {
    section: "Phần 5 · Ứng dụng",
    title: "Mỗi tính năng có một notebook trình bày lại",
    points: ["5 trang: Tư vấn · Tổng quan · Thị trường · Đánh giá mô hình · Dữ liệu", "7 notebook giải thích từng bước, chạy lại được từ đầu", "230 kiểm thử tự động, tất cả đạt"],
    script: [
      "Ứng dụng có năm trang: tư vấn và dự đoán lương, tổng quan thị trường, khám phá kỹ năng theo nghề, đánh giá mô hình, và dữ liệu huấn luyện.",
      "Với mỗi tính năng, nhóm làm một notebook, tức một tài liệu vừa có lời giải thích vừa có mã chạy được, trình bày lại toàn bộ logic phía sau: dữ liệu được xử lý thế nào, biểu đồ được tính ra sao, mô hình được kiểm định thế nào. Các notebook được chạy tự động mỗi lần sửa mã, nên luôn khớp với ứng dụng.",
      "Tất cả các trang dùng chung bộ 1.735 tin thật. Trang Thị trường việc làm cho lọc theo nguồn, nghề và khu vực để xem kỹ năng nào được tuyển nhiều và kỹ năng nào đi kèm lương cao.",
      "Ngoài ra dự án có 230 kiểm thử tự động. Trong đó có những kiểm thử chặn đúng các lỗi đã gặp: thêm kỹ năng không được làm giảm lương, không còn tin giả trong dữ liệu, hồ sơ ít dữ liệu không được hiện con số.",
    ],
  },

  // ───────────────────────── KẾT LUẬN
  { section: "Kết luận", layout: "section", title: "Kết luận", script: ["Em xin chuyển sang phần kết luận."] },
  {
    section: "Kết luận",
    title: "Ba điều rút ra",
    points: ["Kinh nghiệm quyết định lương nhiều nhất; lên Senior là bước nhảy lớn", "Kỹ năng AI, đám mây gắn với lương cao; kỹ năng phổ biến giúp có việc", "Dữ liệu thật quan trọng hơn con số đẹp"],
    script: [
      "Em xin tóm lại ba điều.",
      "Một, về thị trường: kinh nghiệm là thứ quyết định lương nhiều nhất, và bước nhảy lớn nhất là lúc lên Senior.",
      "Hai, về kỹ năng: những kỹ năng gắn với AI và điện toán đám mây gắn với lương cao; những kỹ năng phổ biến như JavaScript hay Java giúp có việc, nhưng không giúp được trả thêm.",
      "Ba, về cách làm: dữ liệu thật quan trọng hơn con số đẹp. Nhóm đã bỏ hơn một nửa dữ liệu vì phát hiện đó là tin giả, chấp nhận kết quả xấu đi, và nói thẳng với người dùng rằng mô hình chưa đạt chuẩn. Em nghĩ đó là điều đáng giá nhất nhóm học được.",
    ],
  },
  {
    section: "Kết luận",
    title: "Hạn chế – nói thật",
    points: ["Chỉ có 1.735 tin thật; đề thi 288 tin là quá nhỏ", "Lương trên tin tuyển dụng, không phải lương thực nhận", "Mô hình chưa đạt chuẩn; nhãn mới được AI duyệt, chưa có người duyệt"],
    script: [
      "Em xin nói thật về hạn chế. Thứ nhất, sau khi bỏ tin giả chỉ còn 1.735 tin thật, đề thi 288 tin là quá nhỏ: đa số nghề chưa chấm riêng được, và chưa đủ bằng chứng để nói mô hình tốt nhất hơn hẳn hai mô hình kia.",
      "Thứ hai, lương ở đây là lương ghi trên tin tuyển dụng, chưa rõ trước hay sau thuế, không phải lương thực nhận. Dữ liệu cũng lệch về Hà Nội.",
      "Thứ ba, mô hình chưa đạt chuẩn production, cấp trưởng nhóm sai nhiều, người mới bị đoán cao khoảng 7%. Mẫu kiểm tra nhãn do AI duyệt, cần người duyệt lại. Và mức tăng lương theo kỹ năng chỉ là quan hệ học từ dữ liệu, không phải lời hứa.",
    ],
  },
  {
    section: "Kết luận",
    title: "Hướng tiếp theo",
    points: ["Thu thập thêm tin thật có lương, nhất là TP.HCM", "Thêm thông tin quy mô công ty để đoán tốt vị trí quản lý", "Mời người duyệt lại nhãn; khảo sát lương thực nhận"],
    script: [
      "Hướng tiếp theo đi thẳng từ các hạn chế. Quan trọng nhất là thu thập thêm tin thật có lương, nhất là ở TP.HCM, vì đây là cách nhiều khả năng nhất để đạt chuẩn. Thêm thông tin quy mô công ty để đoán tốt hơn các vị trí quản lý. Mời người duyệt lại mẫu nhãn. Và nếu có thể, kết hợp khảo sát lương thực nhận, có thông tin giới tính và có sự đồng ý của người tham gia, để đo được công bằng giới.",
    ],
  },
  {
    section: "Kết luận",
    layout: "cover",
    title: "Cảm ơn thầy và các bạn đã lắng nghe",
    subtitle: "Em xin sẵn sàng nhận câu hỏi\nMã nguồn: github.com/theihoz/ML",
    script: [
      "Phần trình bày của em đến đây là hết. Nếu tóm lại trong một câu: nhóm đã biến hàng nghìn tin tuyển dụng lộn xộn thành một công cụ tư vấn lương, và quan trọng hơn, đã kiểm tra nó đủ kỹ để biết khi nào nên tin và khi nào chưa nên tin. Em cảm ơn thầy và các bạn đã lắng nghe, em xin sẵn sàng nhận câu hỏi.",
    ],
  },
];

const QA = [
  {
    q: "Bỏ hơn một nửa dữ liệu, kết quả xấu đi – sao không giữ lại?",
    a: "Vì 2.400 tin đó là tin do máy sinh ra: cùng kiểu đường link \"hist\", đúng 800 tin mỗi trang, kỹ năng ngẫu nhiên, không có mô tả. Chúng dễ đoán hơn tin thật nên làm điểm đẹp giả: mô hình cũ trông như sai 16,5% nhưng chấm riêng trên tin thật là 18%. Mục tiêu là đoán lương tin thật, nên chỉ tin thật mới được dùng để học và để chấm. Cái giá là đề thi còn 288 tin, nhóm ghi rõ trong hạn chế.",
  },
  {
    q: "Mô hình chưa đạt chuẩn production, vậy có dùng được không?",
    a: "Dùng được để tham khảo, và ứng dụng ghi rõ điều đó. Với bốn nghề đông tin (Backend, Kiểm thử, Mobile, Fullstack) và cấp Junior đến Senior, mô hình đạt chuẩn nhóm. Với hồ sơ ít dữ liệu, ứng dụng chỉ hiện khoảng, không hiện con số. Nhóm đã đo và thấy nguyên nhân chính là thiếu tin thật, không phải lỗi gán nhãn; hướng giải quyết là thu thập thêm dữ liệu.",
  },
  {
    q: "Chuẩn 15% và 65% lấy từ đâu?",
    a: "Từ cách Glassdoor và LinkedIn công bố độ chính xác. Glassdoor: một nửa dự đoán lệch dưới 10,2%, 75,3% lệch không quá 20%. Vì họ có lương thực nhận và thông tin công ty, còn nhóm chỉ có lương trên tin tuyển dụng, nên nhóm đặt chuẩn nới hơn; mức của Glassdoor là mục tiêu dài hạn. Ngưỡng được khóa trong code trước khi chấm.",
  },
  {
    q: "Gradient Boosting chỉ thắng 83–91% số lần bootstrap, sao vẫn chọn?",
    a: "Vì nó được chọn theo tiêu chí đã chốt từ trước (sai số thấp nhất trên phần dữ liệu dùng để chọn mô hình), không chọn theo đề thi. Nó cũng hỗ trợ tự nhiên luật \"thêm kỹ năng không giảm lương\". Nhóm nói rõ chưa đủ bằng chứng để khẳng định nó tốt hơn hẳn; cần thêm dữ liệu thật. So với đoán bừa thì chắc chắn tốt hơn (100% số lần).",
  },
  {
    q: "Vì sao không dùng deep learning?",
    a: "Chỉ có khoảng 1.200 tin để học, dạng bảng. Với loại dữ liệu này, các mô hình dựa trên cây quyết định thường tốt hơn, nhanh hơn, dễ giải thích hơn. Mạng nơ-ron phát huy khi có hàng trăm nghìn mẫu hoặc dữ liệu ảnh, âm thanh, văn bản dài.",
  },
  {
    q: "Tại sao chia dữ liệu theo công ty mà không chia ngẫu nhiên?",
    a: "Một công ty đăng nhiều tin gần giống nhau, cùng khung lương. Chia ngẫu nhiên thì mô hình chỉ cần nhớ công ty là đoán đúng – giống ôn đúng đề sẽ thi. Câu hỏi thật của người dùng là về công ty mới, nên đề thi phải gồm công ty chưa từng gặp.",
  },
  {
    q: "Lấy điểm giữa khoảng lương có hợp lý không?",
    a: "Khi không biết người được tuyển nhận mức nào trong khoảng, điểm giữa là giá trị đại diện tự nhiên nhất và là cách nhà tuyển dụng hay nói \"khoảng 20 triệu\". Nhóm vẫn lưu cả hai đầu. Ứng dụng cũng hiện khoảng chứ không chỉ một con số.",
  },
  {
    q: "Tin chỉ ghi \"Tới 30 triệu\" thì đoán đầu dưới thế nào?",
    a: "Ban đầu dùng 70% cố định. Sau khi kiểm tra, nhóm đổi sang học tỉ lệ cao/thấp điển hình của từng trang từ chính các tin ghi đủ hai đầu trong phần dữ liệu học (1,27 đến 1,67), vì mỗi trang có thói quen ghi khoảng khác nhau. Vẫn là giả định, đã ghi trong hạn chế.",
  },
  {
    q: "Học AI tạo sinh có chắc được tăng gần 8 triệu không?",
    a: "Không. Đây là phép thử \"nếu như\" trên mô hình học từ tin tuyển dụng, tức là quan hệ thống kê, không phải nhân quả. Công ty đòi AI tạo sinh có thể là công ty lớn, và quy mô công ty mới là lý do trả cao. Nên hiểu là \"thị trường đang trả cao hơn cho hồ sơ có kỹ năng này\".",
  },
  {
    q: "Mô hình có phân biệt giới tính không?",
    a: "Mô hình không dùng giới tính, nên không thể trả lương khác nhau cho nam và nữ cùng hồ sơ. Nhưng dữ liệu không có giới tính người được tuyển nên không đo được công bằng giới đầy đủ. Nhóm chỉ kiểm được tin có điều kiện giới tính: 7 tin, quá ít để kết luận. Đề xuất: cảnh báo các tin này và khảo sát lương thực nhận nếu muốn đo.",
  },
  {
    q: "Vì sao người mới (Junior) bị đoán cao khoảng 7%?",
    a: "Một phần do mô hình học trên thang logarit nên có xu hướng đoán cao chung khoảng 4%. Phần còn lại nhiều khả năng do lương Junior phân tán mạnh: cùng chức danh nhưng có công ty trả 10 triệu, có công ty trả 20 triệu, mà quy mô công ty không có trong dữ liệu. Nhóm chưa kiểm chứng giả thuyết này và không chỉnh theo đề thi để tránh \"học tủ\".",
  },
  {
    q: "Kết quả kiểm tra nhãn do AI duyệt thì có tin được không?",
    a: "Đó là ước lượng ban đầu, nhóm ghi rõ trong báo cáo. Định dạng file duyệt cho phép người duyệt chỉ cần sửa các cột kết quả rồi chạy lại phép chấm. Kết luận chính – lương và kinh nghiệm đọc đúng, lỗi vai trò và cấp bậc đã sửa thành luật – vẫn có giá trị vì các lỗi tìm được đều cụ thể và kiểm tra được.",
  },
];

const CHEAT = [
  ["Dữ liệu thô", "3 bộ Kaggle · 8.523 tin IT · 36% không ghi lương"],
  ["Tin giả", "2.400 tin do máy sinh (link \"hist\", 800 tin/trang, kỹ năng ngẫu nhiên) → loại"],
  ["Sau làm sạch", "1.735 tin thật · 671 công ty · 23 vị trí · 69 kỹ năng"],
  ["Chia theo công ty", "Học 1.169 · Chọn 278 · Thi 288 tin (121 công ty)"],
  ["Kiểm tra nhãn", "208 tin · lương 100% · vai trò 95% → 99,5% · lần 2: 67 tin, sai 0–3% · do AI duyệt"],
  ["Lương", "Trung vị 25 triệu · trung bình 28,1 · 10% cao nhất trên 47,5"],
  ["Kinh nghiệm", "Spearman 0,70 · <1 năm 13,5 → 5–7 năm 48 triệu"],
  ["Mô hình chọn", "Gradient Boosting, luật đơn điệu theo kinh nghiệm và kỹ năng"],
  ["Sai số", "MAE 6,49 triệu (đoán bừa 11,25) · trung vị sai 16,9% · 55% lệch ≤ 20%"],
  ["Khoảng 80%", "Đúng 83,3% · lương cao chỉ 71%"],
  ["Bootstrap", "GB thắng Ridge 83%, RF 91% → chưa chắc chắn"],
  ["Công bằng", "Junior +7,2% (có ý nghĩa) · HN/HCM không lệch · giới tính không đo được"],
  ["Chuẩn production", "Chưa đạt (cần ≤15% và ≥65%) · Lead trượt · 4 nghề + 3 cấp đạt"],
  ["Kỹ năng tăng lương", "LLM +7,7 · AWS +3,4 · Next.js +2,4 · React Native +2,4 · Kafka +2,2"],
  ["Demo", "Backend HN 3 năm: gross 21–31, điển hình 26, cao hơn 36% tin · Data Engineer: chỉ khoảng 24–60"],
  ["Đối chiếu báo cáo", "TopDev: 8/10 nghề lệch ≤ 15% (Frontend, Mobile còn lệch)"],
];

module.exports = { SLIDES, QA, CHEAT };
