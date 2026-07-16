# coding=utf-8
import json
import logging,os
import socket
import time
import sys
import numpy as np
import cv2
# ==================== 相机 SDK 依赖 ====================
# 当前参考实现使用 RealSense。更换相机时，替换此导入以及
# displayD435() 中标记的“相机 SDK 适配点”，callback() 只需接收 BGR numpy 图像。
import pyrealsense2 as rs

from libs.log_setting import CommonLog
from libs.auxiliary import create_folder_with_date, get_ip, popup_message

cam0_origin_path = create_folder_with_date() # 提前建立好的存储照片文件的目录


logger_ = logging.getLogger(__name__)
logger_ = CommonLog(logger_)

def callback(frame,arm):

    scaling_factor = 2.0
    global count

    cv_img = cv2.resize(frame, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCornersSB(gray, (14, 9), None)
    show_img = cv_img.copy()
    cv2.drawChessboardCorners(show_img, (14, 9), corners, ret)
    cv2.imshow("Capture_Video", show_img)  # 窗口显示，显示名为 Capture_Video

    k = cv2.waitKey(30) & 0xFF  # 每帧数据延时 1ms，延时不能为 0，否则读取的结果会是静态帧

    if k == ord('s'):  # 若检测到按键 ‘s’，打印字符串

        state, pose, joints = send_cmd(arm)
        logger_.info(f'获取状态：{"成功" if state else "失败"}，{f"当前位姿为{pose}" if state else None}')
        if state:

            filename = os.path.join(cam0_origin_path,"poses.txt")
            joint_states_filename = os.path.join(cam0_origin_path,"joint_states.txt")

            with open(filename, 'a+') as f:
                # 将列表中的元素用空格连接成一行
                pose_ = [str(i) for i in pose]
                new_line = f'{",".join(pose_)}\n'
                # 将新行附加到文件的末尾
                f.write(new_line)

            with open(joint_states_filename, 'a+') as f:
                # 将列表中的元素用空格连接成一行
                joints_ = [str(i) for i in joints]
                new_line = f'{",".join(joints_)}\n'
                # 将新行附加到文件的末尾
                f.write(new_line)

            image_path = os.path.join(cam0_origin_path,f"{str(count)}.jpg")
            cv2.imwrite(image_path , cv_img)
            logger_.info(f"===采集第{count}次数据！")

        count += 1

    else:
        pass


def send_cmd(arm, get_pose=True):
    """
    通过机械臂 SDK 读取并归一化标定所需的机械臂状态。

    参数:
    arm: xArm SDK 的 XArmAPI 实例
    get_pose: 保留参数，当前实现始终读取位姿

    返回:
    (success, pose, joints)，其中 pose 的位移单位为米，旋转单位为弧度。
    """

    try:
        # ==================== 机械臂 SDK 适配点 1/4 ====================
        # 以下属性是 xArm SDK 接口。更换机械臂时，在这里改为新 SDK
        # 的位姿、关节角和错误码读取接口，并保持本函数的返回格式不变。
        target_data = arm.position
        joint_data = arm.angles

        if not target_data:
            return False, None, None

        # 检查错误码
        if arm.error_code != 0:
            logger_.error_(f"机械臂报错: {arm.error_code}")
            return False, None, None
        # xArm 位姿格式：[x, y, z, roll, pitch, yaw]，位移为 mm，角度为度。
        # 更换 SDK 时必须核对位姿顺序、旋转表示和单位，最终统一转为 m/rad。
        pose_raw = target_data
        pose_converted = [
            pose_raw[0] / 1000,  # x: 1mm → m
            pose_raw[1] / 1000,  # y: 1mm → m
            pose_raw[2] / 1000,  # z: 1mm → m
            pose_raw[3] * np.pi / 180,  # rx: degree → rad
            pose_raw[4] * np.pi / 180,  # ry: degree → rad
            pose_raw[5] * np.pi / 180   # rz: degree → rad
        ]

        return True, pose_converted, joint_data

    except json.JSONDecodeError:
        logger_.error_("JSON解析错误")
        return False, None, None
    except KeyError as e:
        logger_.error_(f"响应缺少关键字段: {str(e)}")
        return False, None, None
    except Exception as e:
        logger_.error_(f"处理响应时发生错误: {str(e)}")
        return False, None, None
#
def displayD435(robotip):

    # ==================== 相机 SDK 适配点 1/3 ====================
    # 相机创建、彩色流配置和启动。更换相机时替换本区块。
    # 下游约定：每帧最终需转换为 OpenCV BGR 格式的 numpy.ndarray。
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    try:
        pipeline.start(config)
    except Exception as e:
        logger_.error_(f"相机连接异常：{e}")
        popup_message("提醒", "相机连接异常")

        sys.exit(1)

    # ==================== 机械臂 SDK 适配点 2/4 ====================
    # xArm 连接与实例化。更换机械臂时，将此处替换为新 SDK 的连接方式。
    arm = XArmAPI(robotip)
    time.sleep(0.5)

    # ==================== 机械臂 SDK 适配点 3/4 ====================
    # xArm 清除报警/错误、上电以及进入可运动状态的流程。
    # 更换机械臂时，按新 SDK 要求替换整个区块。
    if arm.warn_code != 0:
        arm.clean_warn()
    if arm.error_code != 0:
        arm.clean_error()

    #Enable the robot
    arm.motion_enable(enable=True)
    arm.set_mode(0)
    arm.set_state(0)

    global count
    count = 1

    logger_.info(f"开始手眼标定程序，当前程序版号V1.0.0")



    try:
        while True:
            # ==================== 相机 SDK 适配点 2/3 ====================
            # 相机取帧和 SDK 帧对象到 BGR numpy 图像的转换。
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            callback(color_image,arm=arm)

    finally:
        print("退出程序")
        # ==================== 机械臂 SDK 适配点 4/4 ====================
        # xArm 断开连接接口；更换 SDK 时改为对应的资源释放方法。
        arm.disconnect()
        # ==================== 相机 SDK 适配点 3/3 ====================
        # 相机停止采集/释放资源。更换相机时改为对应 SDK 的关闭方法。
        pipeline.stop()
        cv2.destroyAllWindows()


if __name__ == '__main__':

    robot_ip = get_ip()
    logger_.info(f'robot_ip:{robot_ip}')

    if robot_ip != False:
        # ==================== xArm SDK 导入 ====================
        # 更换机械臂时，从这里替换 SDK 导入，并同步修改上方 4 个适配点。
        from xarm.wrapper import XArmAPI

        displayD435(robot_ip)
