"""
Module for every idrac feature that is only available in
the web interface and can't be used via racadm
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located,
    element_to_be_clickable,
)


def graceful_shutdown(access_cfg):
    """
    Use selenium to access iDRAC web ui and make the system
    shut down gracefully. Unfortunately this is the only way for
    *graceful* shutdown with iDRAC6"""
    # setup selenium driver

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("ignore-certificate-errors")  # because sketchy

    driver = webdriver.Chrome(options=options)

    # go o the idrac web interface login page
    driver.get(f"http://{access_cfg['idrac_address']}")
    # wait until the (usually) last ui element has loaded
    WebDriverWait(driver, 20).until(
        presence_of_element_located((By.XPATH, "//option[text()='This iDRAC']"))
    )

    # find fields for username/pw and the submitting button
    user_input_field = driver.find_element(by=By.XPATH, value="//input[@id='user']")
    pw_input_field = driver.find_element(by=By.ID, value="password")
    submit_button = driver.find_element(by=By.ID, value="btnOK")

    # fill fields out and submit
    user_input_field.send_keys(access_cfg["username"])
    pw_input_field.send_keys(access_cfg["password"])
    submit_button.click()

    # because for some reason everything is in weird frames, here some switcharoo
    navbar_frame = WebDriverWait(driver, 20).until(
        presence_of_element_located((By.XPATH, "//frame[@src='snb.html']"))
    )
    driver.switch_to.frame(navbar_frame)

    # find the "Power" tab on the navbar and click it
    navbar_power = WebDriverWait(driver, 10).until(
        presence_of_element_located((By.XPATH, "//tbody/tr/td/a[text()='Power']"))
    )
    navbar_power.click()

    # more frame fuckery & wait until the incredibly slow UI has loaded
    driver.switch_to.default_content()
    power_control_frame = WebDriverWait(driver, 20).until(
        presence_of_element_located((By.XPATH, "//frame[@src='sysSummaryData.html']"))
    )
    driver.switch_to.frame(power_control_frame)

    # wait until the shutdown selection has appeared and is clickable
    graceful_shutdown_select = WebDriverWait(driver, 10).until(
        presence_of_element_located((By.XPATH, "//input[@value='shutdown']"))
    )
    WebDriverWait(driver, 10).until(element_to_be_clickable(graceful_shutdown_select))

    # select graceful shutdown and submit, finally confirm the alert
    graceful_shutdown_select.click()
    submit_power_action_button = driver.find_element(
        by=By.XPATH, value="//div[@class='button_clear']/a[@class='container_button']"
    )
    submit_power_action_button.click()
    driver.switch_to.alert.accept()

    # find the frame for logout button
    driver.switch_to.default_content()
    top_nav_frame = WebDriverWait(driver, 15).until(
        presence_of_element_located((By.XPATH, "//frame[@src='globalnav.html']"))
    )
    driver.switch_to.frame(top_nav_frame)
    # find and click logout
    logout_button = driver.find_element(
        by=By.XPATH, value="//a[normalize-space(text())='Logout']"
    )
    logout_button.click()  # make it clean for iDRAC UwU
    # and close chrome
    driver.quit()
