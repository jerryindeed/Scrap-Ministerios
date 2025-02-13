from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service   
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time 
import os
import pandas as pd

# Set the path to the ChromeDriver executable   
chrome_options = Options()  
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu") 

#Set download path
chrome_options.add_experimental_option("prefs", {
  "download.default_directory": "D:\\Proyectos\\UC\\CSV downloads",
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

# Set the path to the ChromeDriver executable   
service = Service(ChromeDriverManager().install())  
driver = webdriver.Chrome(service=service, options=chrome_options)

# Eliminar archivos CSV previos antes de comenzar
folder_path = "./"  # Carpeta donde se guardarán los CSV (cambiar si es necesario)
for file in os.listdir(folder_path):
    if file.endswith(".csv"):
        os.remove(os.path.join(folder_path, file))
        print(f"🗑 Archivo eliminado: {file}")

# URL de la página
URL = "https://www.portaltransparencia.cl/PortalPdT/directorio-de-organismos-regulados/?org=AC001"

# Lista de años y meses a recorrer
años = ["2017","2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Función para hacer clic en "Personal a Contrata"
def ir_a_personal_a_contrata():
    try:
        elemento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Personal a Contrata')]"))
        )
        elemento.click()
        print("✔ Se hizo clic en 'Personal a Contrata'")
    except:
        print("❌ No se encontró el botón 'Personal a Contrata'")

# Abrir la página
driver.get(URL)
ir_a_personal_a_contrata()

# URL principal
URL = "https://www.portaltransparencia.cl/PortalPdT/directorio-de-organismos-regulados/?org=AC001"

# Función para volver a "Personal a Contrata"
def ir_a_personal_a_contrata():
    try:
        elemento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Personal a Contrata')]"))
        )
        elemento.click()
        time.sleep(2)
    except:
        print("❌ No se encontró 'Personal a Contrata'")

# Lista de años y meses a recorrer
años = ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Iterar sobre cada año
for año in años:
    try:
        # Seleccionar año
        year_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{año}')]"))
        )
        year_button.click()
        time.sleep(2)
        print(f"✔ Se hizo clic en el año {año}")

        # Iterar sobre cada mes dentro del año
        for mes in meses:
            try:
                # Seleccionar mes
                month_button = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{mes}')]"))
                )
                month_button.click()
                time.sleep(2)
                print(f"✔ Se hizo clic en el mes {mes}")

                datos_tabla = []  # Lista para almacenar los datos de la tabla

                total_filas = 0  # Acumulador para contar todas las filas

                while True:
                    # Encontrar la tabla
                    tabla = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//table"))
                    )

                    # Obtener nombres de las columnas desde thead
                    columnas = [col.text.strip() for col in tabla.find_elements(By.XPATH, ".//thead/tr/th")]
                    if not columnas:  # Si no hay en thead, intentamos en tbody
                        columnas = [col.text.strip() for col in tabla.find_elements(By.XPATH, ".//tbody/tr[1]/td")]

                    # Obtener las filas de tbody
                    filas = tabla.find_elements(By.XPATH, ".//tbody/tr")
                    for fila in filas:
                        datos_fila = [celda.text.strip() for celda in fila.find_elements(By.XPATH, ".//td")]
                        if len(datos_fila) == len(columnas):  # Asegurar que coincide con las columnas
                            datos_tabla.append(datos_fila)


                    # Verificar si hay un botón "Siguiente" y si no está deshabilitado
                    try:
                        next_button = driver.find_element(By.CLASS_NAME, "ui-paginator-next")

                        # Si el botón tiene la clase "ui-state-disabled", se detiene el bucle
                        if "ui-state-disabled" in next_button.get_attribute("class"):
                            print("⏹ Última página alcanzada.")
                            break

                        # Si no está deshabilitado, hacer clic y continuar
                        next_button.click()
                        time.sleep(3)  # Esperar a que la página cargue

                    except:
                        print("❌ No se encontró el botón 'Siguiente', terminando paginación.")
                        break

                 # Crear DataFrame con los datos recopilados
                df = pd.DataFrame(datos_tabla, columns=columnas)

                # Guardar el DataFrame en CSV
                nombre_archivo = f"datos_{año}_{mes}.csv"
                df.to_csv(nombre_archivo, index=False, encoding="utf-8-sig")
                print(f"📂 Archivo guardado: {nombre_archivo}")

                # Refrescar la página
                driver.get(URL)
                time.sleep(2)

                # Volver a "Personal a Contrata"
                ir_a_personal_a_contrata()

                # Volver a seleccionar el año
                year_button = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{año}')]"))
                )
                year_button.click()
                time.sleep(2)

            except:
                print(f"❌ No se encontró el mes {mes}, continuando...")

    except:
        print(f"❌ No se encontró el año {año}, continuando...")


# Cerrar el navegador al terminar
driver.quit()







 
