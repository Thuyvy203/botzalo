import re
from zlapi.models import Message, ThreadType

def format_number(x):
    """Định dạng số: nếu là số nguyên, trả về dạng integer, nếu không trả về dạng float."""
    if x.is_integer():
        return str(int(x))
    return str(x)

def calculate_expression(match):
    """
    Nhận một match từ regex với 3 nhóm:
      - Nhóm 1: Số thứ nhất (có thể số nguyên hoặc số thực)
      - Nhóm 2: Toán tử (+, -, *, x, nhân, /, :, chia)
      - Nhóm 3: Số thứ hai (có thể số nguyên hoặc số thực)
    Tính toán và trả về chuỗi kết quả với định dạng hợp lý.
    """
    try:
        a = float(match.group(1))
        op = match.group(2).lower()  # chuyển về chữ thường để xử lý
        b = float(match.group(3))
        if op == '+':
            result = a + b
        elif op == '-':
            result = a - b
        elif op in ('*', 'x', 'nhân', "×"):
            result = a * b
        elif op in ('/', ':', 'chia'):
            if b == 0:
                return "Lỗi: Không thể chia cho 0."
            result = a / b
        else:
            return "Phép tính không hợp lệ."
        
        formatted_a = format_number(a)
        formatted_b = format_number(b)
        formatted_result = format_number(result)
        return f"Kết quả: {formatted_a} {op} {formatted_b} = {formatted_result}"
    except Exception as e:
        return f"Lỗi khi tính toán: {e}"

# Biểu thức chính quy để nhận diện các phép tính.
# Chú ý: Số có thể chứa dấu . làm phân cách thập phân.
# Toán tử có thể là +, -, *, x, nhân, /, :, chia
math_pattern = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(\+|\-|\*|x|nhân|/|:|chia)\s*(\d+(?:\.\d+)?)\s*\??\s*$",
    re.IGNORECASE
)

def handle_math_message(message, user_name="bạn"):
    """
    Kiểm tra tin nhắn có chứa biểu thức tính toán không.
    Nếu có, thực hiện tính toán và trả về kết quả.
    Nếu không khớp, trả về None để cho phép xử lý các loại tin nhắn khác.
    """
    match = math_pattern.match(message)
    if match:
        return calculate_expression(match)
    return None

def get_mitaizl():
    """
    Trả về dictionary chứa hàm xử lý phép tính.
    Sử dụng key 'calculate' để gọi hàm handle_math_message.
    """
    return {
        'calculate': handle_math_message
    }
