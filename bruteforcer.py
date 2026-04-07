from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from datetime import datetime
import json
import os

def init_interactive():
    print("▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓")
    print("MOODLE LESSONS BRUTEFORCER")
    print("made by futsurignnahateu <3")
    print("▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓")
    
    while True:
        debug_input = input("\nНужны ли детальные DEBUG логи? (y/n): ").strip().lower()
        if debug_input in ['y', 'yes', 'д', 'да']:
            debug_mode = True
            break
        elif debug_input in ['n', 'no', 'н', 'нет']:
            debug_mode = False
            break
        else:
            print("   [ERROR] Введите 'y' (да) или 'n' (нет)")
    
    return debug_mode

DEBUG_MODE = init_interactive()

log_filename = f"bruteforcer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

if DEBUG_MODE:
    print("\n[OK] DEBUG режим включен - будут логированы все детали")
else:
    print("\n[INFO] DEBUG режим отключен - только основная информация")

logger.info(f"Логи сохраняются в файл: {log_filename}")
logger.info(f"DEBUG режим: {'ВКЛЮЧЁН' if DEBUG_MODE else 'ОТКЛЮЧЁН'}")

def ask_read_lectures():
    while True:
        read_input = input("\nЧитать лекции (ждать вопросы)? (y/n): ").strip().lower()
        if read_input in ['y', 'yes', 'д', 'да']:
            return True
        elif read_input in ['n', 'no', 'н', 'нет']:
            return False
        else:
            print("   [ERROR] Введите 'y' (да) или 'n' (нет)")

READ_LECTURES = ask_read_lectures()
logger.info(f"Читать лекции: {'ДА' if READ_LECTURES else 'НЕТ'}")

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# options.add_argument("--headless")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_answer_options():
    radios = driver.find_elements(By.NAME, "answerid")
    options = {}
    for radio in radios:
        try:
            value = radio.get_attribute("value")
            text_elem = radio.find_element(By.XPATH, "./following-sibling::p | ./parent::label/p")
            text = text_elem.text.strip()
        except:
            value = radio.get_attribute("value")
            text = f"Вариант {value}"
        options[value] = text
        logger.debug(f"  Вариант {value}: {text[:60]}")
    logger.debug(f"get_answer_options: найдено {len(options)} вариантов")
    return options

def is_question_page():
    radios = driver.find_elements(By.NAME, "answerid")
    result = len(radios) > 0
    logger.debug(f"is_question_page: {result} (найдено радиокнопок: {len(radios)})")
    return result

def is_wrong_answer_page():
    page = driver.page_source.lower()
    has_ваш_ответ = "ваш ответ" in page
    has_не_совсем = "не совсем правильно" in page
    has_неправильный = "это неправильный ответ" in page
    result = has_ваш_ответ or has_не_совсем or has_неправильный
    logger.debug(f"is_wrong_answer_page: {result} (ваш_ответ={has_ваш_ответ}, не_совсем={has_не_совсем}, неправильный={has_неправильный})")
    return result

def safe_click(element):
    try:
        logger.debug(f"safe_click: обычный клик")
        element.click()
    except Exception as e:
        logger.debug(f"safe_click: обычный клик не сработал, пробуем JS: {e}")
        driver.execute_script("arguments[0].click();", element)

def click_retry_after_wrong():
    try:
        logger.info("click_retry_after_wrong: ищём кнопку повторной попытки")
        retry_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(.,'попробовать еще раз') or contains(.,'попробовать ещё раз')"
                " or contains(.,'хотелось бы попробовать еще раз') or contains(.,'хотелось бы попробовать ещё раз')]"
            ))
        )
        logger.info(f"click_retry_after_wrong: найдена кнопка: {retry_btn.text}")
        safe_click(retry_btn)
        time.sleep(0.5)
        
        logger.info("click_retry_after_wrong: ждём загрузки формы вопроса")
        WebDriverWait(driver, 5).until(
            lambda d: len(d.find_elements(By.NAME, "answerid")) > 0
        )
        logger.info("click_retry_after_wrong: форма вопроса загружена успешно")
        print("   [OK] Форма вопроса загружена, готово к повторной попытке")
        return True
    except Exception as e:
        logger.error(f"click_retry_after_wrong: ошибка - {e}")
        print(f"   [ERROR] Ошибка при загрузке формы повторной попытки: {e}")
        return False

def find_submit_or_continue_button():
    candidates = [
        (By.ID, "id_submitbutton"),
        (By.XPATH, "//input[contains(@value,'Отправить') or contains(@value,'Продолжить')]"),
        (By.XPATH, "//button[contains(text(),'Отправить') or contains(text(),'Продолжить')]"),
    ]
    for by, value in candidates:
        elems = driver.find_elements(by, value)
        if elems:
            logger.debug(f"find_submit_or_continue_button: найдена по селектору {by}={value}, текст={elems[0].text}")
            return elems[0]
    logger.warning("find_submit_or_continue_button: кнопка не найдена!")
    return None

def click_continue():
    try:
        logger.info("click_continue: ищём кнопку 'Продолжить' или 'Дальше'")
        continue_btn = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//input[@value='Продолжить' or @value='Дальше' or contains(@value,'Продолжить') or contains(@value,'Дальше')]"
                "| //button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'продолжить') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'дальше')]"
            ))
        )
        btn_text = continue_btn.text if hasattr(continue_btn, 'text') else continue_btn.get_attribute('value')
        logger.info(f"click_continue: кнопка найдена: {btn_text}")
        continue_btn.click()
        logger.info("click_continue: кнопка нажата [OK]")
        print("   -> Нажали '" + btn_text.strip() + "'")
        time.sleep(0.2)
        return True
    except Exception as e:
        logger.debug(f"click_continue: кнопка не найдена - {e}")
        time.sleep(0.5)
        return False

def save_credentials(email, password, filename="credentials.json"):
    try:
        credentials = {
            "email": email,
            "password": password
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(credentials, f, ensure_ascii=False, indent=2)
        logger.info(f"save_credentials: учётные данные сохранены в файл {filename}")
    except Exception as e:
        logger.error(f"save_credentials: ошибка при сохранении учётных данных - {e}")

def load_credentials(filename="credentials.json"):
    try:
        if not os.path.exists(filename):
            logger.info(f"load_credentials: файл учётных данных {filename} не найден")
            return None, None
        
        with open(filename, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
        
        email = credentials.get("email", "")
        password = credentials.get("password", "")
        
        logger.info(f"load_credentials: учётные данные загружены из файла {filename}")
        return email, password
    except Exception as e:
        logger.error(f"load_credentials: ошибка при загрузке учётных данных - {e}")
        return None, None

def ask_credentials():
    print("УЧЁТНЫЕ ДАННЫЕ MOODLE")
    
    email = input("Введите email/логин: ").strip()
    if not email:
        logger.error("Email не введён")
        print("[ERROR] Email не может быть пустым!")
        return None, None
    
    password = input("Введите пароль: ").strip()
    if not password:
        logger.error("Пароль не введён")
        print("[ERROR] Пароль не может быть пустым!")
        return None, None
    
    logger.info(f"Пользователь ввёл email: {email}")
    logger.info("Пароль введён")
    
    # Сохраняем учётные данные
    save_credentials(email, password)
    print("[OK] Учётные данные сохранены локально")
    
    return email, password

def auto_login_if_on_login_page(email, password):
    """Автоматически логиниться если браузер на странице логина"""
    try:
        current_url = driver.current_url
        
        # Проверяем, находимся ли мы на странице логина https://vec.etu.ru/moodle/login/index.php
        if "vec.etu.ru/moodle/login" not in current_url.lower():
            logger.debug(f"auto_login_if_on_login_page: не на странице логина (URL: {current_url})")
            return False
        
        logger.info("auto_login_if_on_login_page: обнаружена страница логина, начинаем авторизацию")
        print("\n[INFO] Обнаружена страница логина, авторизуюсь автоматически...")
        
        # Ищём поле для ввода email/логина
        logger.info("auto_login_if_on_login_page: ищём поле для ввода email/логина")
        email_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        logger.debug("auto_login_if_on_login_page: поле email найдено")
        
        # Ищём поле для ввода пароля
        logger.info("auto_login_if_on_login_page: ищём поле для ввода пароля")
        password_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        logger.debug("auto_login_if_on_login_page: поле пароля найдено")
        
        # Вводим email
        logger.info(f"auto_login_if_on_login_page: вводим email/логин")
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(0.3)
        
        # Вводим пароль
        logger.info(f"auto_login_if_on_login_page: вводим пароль")
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(0.3)
        
        # Ищём кнопку входа
        logger.info("auto_login_if_on_login_page: ищём кнопку входа")
        login_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "loginbtn"))
        )
        logger.debug("auto_login_if_on_login_page: кнопка входа найдена")
        
        # Нажимаем кнопку входа
        logger.info("auto_login_if_on_login_page: нажимаем кнопку входа")
        login_btn.click()
        print(f"[OK] Авторизация выполнена")
        
        # Ждём загрузки страницы
        logger.info("auto_login_if_on_login_page: ждём загрузки страницы после входа")
        time.sleep(2)
        
        logger.info(f"auto_login_if_on_login_page: авторизация завершена, новый URL: {driver.current_url}")
        return True
        
    except Exception as e:
        logger.error(f"auto_login_if_on_login_page: ошибка при авторизации - {e}")
        print(f"[ERROR] Ошибка при автоматической авторизации: {e}")
        return False

def main():
    logger.info("="*80)
    logger.info("Запуск MOODLE LESSON BRUTE FORCER")
    
    # Загружаем или запрашиваем учётные данные
    email, password = load_credentials()
    if not email or not password:
        logger.info("main: учётные данные не найдены, запрашиваем у пользователя")
        email, password = ask_credentials()
        if not email or not password:
            logger.error("main: не удалось получить учётные данные")
            print("[ERROR] Не удалось получить учётные данные, завершаю работу")
            return
    else:
        logger.info("main: учётные данные загружены из файла")
        print("[OK] Учётные данные загружены из сохранённого файла")
    
    print("\nОткрываю браузер...")
    driver.get("about:blank")
    logger.info("Браузер открыт")
    time.sleep(0.5)
    
    print("\nИнструкции:")
    print("   1. В открытом браузере перейдите на первую страницу лекции")
    print("   2. Убедитесь, что вы на первой странице теста")
    print("   3. Вернитесь сюда в терминал и нажмите Enter")
    input("\nКогда готово, нажмите Enter: ")
    
    current_url = driver.current_url
    logger.info(f"Пользователь готов. Текущий URL: {current_url}")
    
    # Проверяем, не на странице ли логина
    if "vec.etu.ru/moodle/login" in current_url.lower():
        logger.info("main: пользователь находится на странице логина, выполняю автоматическую авторизацию")
        if not auto_login_if_on_login_page(email, password):
            logger.error("main: автоматическая авторизация не удалась")
            print("[ERROR] Не удалось авторизоваться автоматически")
            return
        time.sleep(1)
    
    print(f"\n[OK] Начинаю разбор лекции...")
    logger.info("="*80)
    logger.info(f"Запуск авто-прохождения лекции")
    logger.info(f"URL: {driver.current_url}")

    question_count = 0
    no_questions_warned = False

    while True:
        logger.info("="*80)
        logger.info(f"Итерация цикла #{question_count + 1}, URL: {driver.current_url}")
        logger.debug(f"Page title: {driver.title}")
        
        # Проверяем, не произошел ли редирект на страницу логина
        if "vec.etu.ru/moodle/login" in driver.current_url.lower():
            logger.warning("main: обнаружен редирект на страницу логина, выполняю автоматическую авторизацию")
            print("\n[WARNING] Обнаружен редирект на страницу логина")
            if not auto_login_if_on_login_page(email, password):
                logger.error("main: автоматическая авторизация не удалась")
                print("[ERROR] Не удалось авторизоваться автоматически, пожалуйста авторизуйтесь вручную")
                input("Когда авторизация завершена, нажмите Enter: ")
                time.sleep(1)
            else:
                time.sleep(1)
        
        if not is_question_page():
            if READ_LECTURES:
                if not no_questions_warned:
                    print("\n[WARNING] Вопросы не найдены на странице!")
                    print("   Пролистайте лекцию до следующей страницы с вопросами...\n")
                    logger.info("Вопросы не найдены на странице, ожидаем вопросов...")
                    no_questions_warned = True
                time.sleep(0.5)
                continue
            else:
                logger.info("Режим: пролистывание лекции (READ_LECTURES=False). Автоматически нажимаю 'Продолжить'")
                print(".", end="", flush=True)
                if not click_continue():
                    logger.info("Кнопки 'Продолжить' не найдено, продолжаем")
                    time.sleep(0.5)
                continue
        
        if is_question_page():
            question_count += 1
            logger.info(f"Вопрос #{question_count}")
            
            answer_options = get_answer_options()
            total_options = len(answer_options)
            if DEBUG_MODE:
                print(f"\nВопрос #{question_count} - найдено вариантов: {total_options}")
            logger.info(f"Найдено {total_options} вариантов ответа")

            answered_correctly = False
            attempt = 0

            for option_value, option_text in answer_options.items():
                attempt += 1
                logger.info(f"--- Попытка {attempt}/{total_options} ---")
                logger.info(f"Выбираем вариант: {option_text[:80]}")
                if DEBUG_MODE:
                    print(f"   Пробуем {attempt}/{total_options}: {option_text[:80]}...")
                
                radios = driver.find_elements(By.NAME, "answerid")
                radio_to_click = None
                for radio in radios:
                    if radio.get_attribute("value") == option_value:
                        radio_to_click = radio
                        break
                
                if not radio_to_click:
                    logger.warning(f"Вариант {option_value} больше не найден на странице")
                    if DEBUG_MODE:
                        print(f"   [WARNING] Вариант {option_value} не найден")
                    continue
                
                safe_click(radio_to_click)
                logger.debug(f"Радиокнопка {option_value} кликнута")
                time.sleep(0.2)

                logger.info("Ищём кнопку отправки ответа")
                submit = find_submit_or_continue_button()
                if not submit:
                    logger.error("Кнопка отправки не найдена")
                    if DEBUG_MODE:
                        print("   [ERROR] Не найдена кнопка отправки/продолжения")
                    break
                safe_click(submit)
                logger.info(f"Кнопка отправки нажата, ждём ответа сервера")
                try:
                    WebDriverWait(driver, 10).until(EC.staleness_of(submit))
                    logger.debug("Старый элемент кнопки был удалён из DOM")
                except:
                    pass
                    logger.debug("Элемент кнопки остался в DOM")
                time.sleep(0.5)
                logger.info(f"Текущий URL после отправки: {driver.current_url}")

                logger.info("Проверяем, правильный ли ответ")
                if is_wrong_answer_page():
                    if DEBUG_MODE:
                        print("   [FAIL] Неверно")
                    logger.warning(f"Вариант '{option_text}' оказался неправильным")
                    if not click_retry_after_wrong():
                        logger.info("Попытка повторить неудачна, пробуем клик 'Продолжить'")
                        if not click_continue():
                            logger.error("Ни кнопка повторной попытки, ни 'Продолжить' не найдены")
                            if DEBUG_MODE:
                                print("   [ERROR] Нет кнопки повторной попытки или 'Продолжить'")
                            break
                    logger.info("Обновляем список вариантов после повторной попытки")
                    answer_options = get_answer_options()
                    logger.info("Продолжаем со следующего варианта")
                    continue
                else:
                    if DEBUG_MODE:
                        print("   [OK] ПРАВИЛЬНО!")
                    logger.info(f"[OK] Вариант '{option_text}' ПРАВИЛЬНЫЙ!")
                    answered_correctly = True
                    logger.info("Ищём кнопку 'Продолжить' после верного ответа")
                    click_continue()
                    time.sleep(0.5)
                    break

            if not answered_correctly:
                logger.warning(f"Вопрос {question_count} не был решен, переходим к следующему")
                continue

        else:
            logger.info("Контент-страница (без вопроса)")
            if DEBUG_MODE:
                print("Контент-страница (без вопроса)")
            if not click_continue():
                logger.info("Кнопки 'Продолжить' не найдено на контент-странице")
                if is_question_page():
                    logger.warning("На странице остались вопросы, несмотря на отсутствие кнопки 'Продолжить'!")
                    if DEBUG_MODE:
                        print("[WARNING] На странице найдены вопросы, продолжаем")
                    continue
                else:
                    logger.info("[OK] Нет вопросов и нет кнопки 'Продолжить' - лекция пройдена")
                    if DEBUG_MODE:
                        print("[OK] Лекция пройдена полностью!")
                    print("\n[OK] ЛЕКЦИЯ ПРОЙДЕНА - вопросов не найдено")
                    break

        time.sleep(0.3)

    logger.info("="*80)
    logger.info(f"[OK] Скрипт завершён. Пройдено вопросов: {question_count}")
    print(f"\n[OK] ГОТОВО - пройдено вопросов: {question_count}")
    print(f"[INFO] Логи сохранены в файл: {log_filename}")
    
    input("\nНажмите Enter для закрытия браузера...")

if __name__ == "__main__":
    try:
        main()
    finally:
        driver.quit()
