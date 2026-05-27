#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""截取系统界面截图用于PPT"""
import subprocess, sys, os, time

# 安装selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'selenium', '--quiet'])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

# 截图保存目录
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshots():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1440,900')
    options.add_argument('--force-device-scale-factor=2')  # 2x DPI for sharper images
    
    try:
        driver = webdriver.Chrome(options=options)
    except Exception:
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'webdriver-manager', '--quiet'])
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"Cannot start Chrome: {e}")
            return
    
    wait = WebDriverWait(driver, 10)
    base_url = 'http://127.0.0.1:5000'
    
    pages = [
        ('homepage', '/', '首页'),
        ('login', '/auth/login', '登录页'),
        ('teacher_dashboard', '/teacher_dashboard', '教师仪表盘'),
        ('student_dashboard', '/student_dashboard', '学生仪表盘'),
        ('analysis', '/analysis/', '数据分析'),
        ('student_portrait', '/analysis/student_portrait', '学生画像'),
        ('knowledge_point', '/analysis/knowledge_point', '知识点分析'),
        ('advanced_analysis', '/analysis/advanced_analysis', '高级分析'),
        ('intelligent_assistant', '/intelligent_assistant/', '智能助手'),
        ('learning_plan', '/student/learning_plan', '学习计划'),
    ]
    
    # 先登录教师账号
    driver.get(f'{base_url}/auth/login')
    time.sleep(2)
    try:
        username_input = driver.find_element(By.NAME, 'username')
        password_input = driver.find_element(By.NAME, 'password')
        username_input.send_keys('admin')
        password_input.send_keys('admin123')
        # 查找提交按钮
        submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
        submit_btn.click()
        time.sleep(3)
        print("Logged in as admin")
    except Exception as e:
        print(f"Login attempt: {e}")
    
    # 截取各页面
    for name, path, desc in pages:
        try:
            driver.get(f'{base_url}{path}')
            time.sleep(3)
            filepath = os.path.join(SCREENSHOT_DIR, f'{name}.png')
            driver.save_screenshot(filepath)
            print(f"Screenshot saved: {name} ({desc})")
        except Exception as e:
            print(f"Error capturing {name}: {e}")
    
    # 尝试登录学生账号截取学生端
    try:
        driver.get(f'{base_url}/auth/login')
        time.sleep(2)
        # 先登出
        driver.get(f'{base_url}/auth/logout')
        time.sleep(2)
        driver.get(f'{base_url}/auth/login')
        time.sleep(2)
        username_input = driver.find_element(By.NAME, 'username')
        password_input = driver.find_element(By.NAME, 'password')
        username_input.send_keys('student1')
        password_input.send_keys('password')
        submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
        submit_btn.click()
        time.sleep(3)
        
        student_pages = [
            ('student_learning_center', '/student/start_learning', '学生学习中心'),
            ('student_practice', '/student/special_practice', '专项练习'),
        ]
        for name, path, desc in student_pages:
            try:
                driver.get(f'{base_url}{path}')
                time.sleep(3)
                filepath = os.path.join(SCREENSHOT_DIR, f'{name}.png')
                driver.save_screenshot(filepath)
                print(f"Screenshot saved: {name} ({desc})")
            except Exception as e:
                print(f"Error capturing {name}: {e}")
    except Exception as e:
        print(f"Student login attempt: {e}")
    
    driver.quit()
    print(f"\nAll screenshots saved to: {SCREENSHOT_DIR}")

if __name__ == '__main__':
    take_screenshots()
