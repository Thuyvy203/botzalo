import time
import os
import json
import requests
from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import *
from threading import Thread
from datetime import datetime
import random

# Giả sử bạn đã định nghĩa hàm remove_member_data trong một module nào đó,
# hoặc bạn có thể định nghĩa ngay ở đây nếu muốn:
def remove_member_data(thread_id, member_id):
    """
    Xóa dữ liệu thống kê (daily và weekly) của thành viên khỏi nhóm chat.
    Sau đó lưu lại file thống kê.
    """
    global message_stats
    if thread_id in message_stats:
        for period in ["daily", "weekly"]:
            if member_id in message_stats[thread_id][period]:
                del message_stats[thread_id][period][member_id]
        # Sau đó lưu lại file nếu cần
        with open("message_stats.json", "w", encoding="utf-8") as f:
            json.dump(message_stats, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Đã xóa dữ liệu của member {member_id} ở thread {thread_id}")

# Thông tin phiên bản và người tạo
des = {
    'version': "1.0.2",
    'credits': "thịnh",
    'description': "i"
}

# Danh sách màu sắc hex
bright_colors = [
    "#FFDD57",  # Vàng sáng
    "#FF6F61",  # Đỏ sáng
    "#FFB74D",  # Cam sáng
    "#5DADE2",  # Xanh dương sáng
    "#00A1FF",  # Hồng sáng
    "#F7DC6F",  # Vàng chanh sáng
    "#FFC700",  # Xanh mint sáng
    "#DA00FF",  # Tím nhạt sáng
    "#002BFF",  # Đỏ hồng sáng
    "#FBFF00",
    "#4FFF00",
]

def welcome(self, event_data, event_type):
    def send():
        if event_type == GroupEventType.UNKNOWN:
            return

        print(event_data)
        current_time = datetime.now()
        formatted_time = current_time.strftime("%d/%m/%Y [%H:%M:%S]")

        thread_id = event_data.get('groupId')
        if not thread_id:
            print("Lỗi: Không tìm thấy 'groupId' trong event_data")
            return

        group_info = self.fetchGroupInfo(thread_id)
        total_members = group_info.get('gridInfoMap', {}).get(thread_id, {}).get('totalMember', 0)

        if event_type == GroupEventType.JOIN:
            group_name = event_data.get('groupName', "nhóm")
            for i, member in enumerate(event_data.get('updateMembers', [])):
                member_id = member.get('id')
                member_name = member.get('dName')
                avatar_url = member.get('avatar')

                text_lines = [
                    '[ MITAI PROJECT NOTIFICATION GROUP ]',
                    f'> Chào mừng: @{member_name}',
                    f'> Bạn là thành viên thứ: {total_members + i}',
                    f'> Đã tham gia nhóm: {group_name}.'
                ]

                # Gửi tin nhắn văn bản với màu sắc khác nhau cho từng dòng
                message_styles = []
                for j, line in enumerate(text_lines):
                    color = random.choice(bright_colors)  # Chọn màu ngẫu nhiên cho mỗi dòng
                    message_styles.append(MessageStyle(
                        offset=sum(len(text_lines[k]) + 1 for k in range(j)),
                        length=len(line),
                        style='color',
                        color=color,
                        auto_format=False  # Không sử dụng fontSize
                    ))

                msg = Message(text='\n'.join(text_lines), style=MultiMsgStyle(message_styles))
                self.send(msg, thread_id, ThreadType.GROUP, ttl=70000)

                # Gửi thẻ (card) cho thành viên
                if member_id and avatar_url:
                    self.sendBusinessCard(userId=member_id, qrCodeUrl=avatar_url, thread_id=thread_id, thread_type=ThreadType.GROUP, ttl=70000)

        elif event_type in {GroupEventType.LEAVE, GroupEventType.REMOVE_MEMBER}:
            group_name = event_data.get('groupName', "nhóm")
            member_info = event_data.get('updateMembers', [{}])[0]
            member_name = member_info.get('dName', "thành viên")
            member_id = member_info.get('id')
            avatar_url = member_info.get('avatar')

            text_lines = [
                '[ MITAI PROJECT NOTIFICATION GROUP ]',
                f'> {member_name} bị xoá khỏi nhóm',
                f'> Nhóm: {group_name}',
                f'> Vào lúc: {formatted_time}',
                f'> Tổng thành viên còn lại: {total_members - 1}'
            ]

            # Gửi tin nhắn văn bản với màu sắc khác nhau cho từng dòng
            message_styles = []
            for j, line in enumerate(text_lines):
                color = random.choice(bright_colors)  # Chọn màu ngẫu nhiên cho mỗi dòng
                message_styles.append(MessageStyle(
                    offset=sum(len(text_lines[k]) + 1 for k in range(j)),
                    length=len(line),
                    style='color',
                    color=color,
                    auto_format=False  # Không sử dụng fontSize
                ))

            msg = Message(text='\n'.join(text_lines), style=MultiMsgStyle(message_styles))
            self.send(msg, thread_id, ThreadType.GROUP, ttl=70000)

            # Gửi thẻ (card) cho thành viên
            if member_id and avatar_url:
                self.sendBusinessCard(userId=member_id, qrCodeUrl=avatar_url, thread_id=thread_id, thread_type=ThreadType.GROUP, ttl=70000)

            # Sau khi thông báo, xóa dữ liệu thống kê của thành viên đó
            try:
                # Nếu remove_member_data đã được định nghĩa trong cùng file hoặc import từ module khác
                remove_member_data(thread_id, str(member_id))
            except Exception as e:
                print(f"[DEBUG] Lỗi khi xóa dữ liệu thống kê của thành viên {member_id}: {e}")

    thread = Thread(target=send)
    thread.start()

def get_mitaizl():
    return {
        'welcome': welcome  
    }
