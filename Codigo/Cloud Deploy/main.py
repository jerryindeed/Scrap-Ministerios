# Libraries to use
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.cloud import storage
import threading
from urllib.parse import quote as url_quote
import pandas as pd
import time
import io
import os

app = Flask(__name__)

# Configura ChromDriver de modo headless para correr sin problemas
def get_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return chrome_options

# Conectamos al repo de GCS con su bucket correspondiente
storage_client = storage.Client(project="ministerios-test")
bucket = storage_client.bucket("transparencia-ministerios1")

def upload_to_gcs(df, filename):
    """Upload a DataFrame to Google Cloud Storage as CSV"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    blob = bucket.blob(filename)
    blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")
    return f"gs://transparencia-ministerios1/{filename}"

def main():
    print("¡Iniciando proceso de scraping!")
    try:
        # Inicia webdriver
        chrome_options = get_chrome_options()
        driver = webdriver.Chrome(options=chrome_options)
        
        # Tomamos la organizacion de GCS
        organizations_blob = bucket.blob("Listado_organizaciones_estado.csv")
        organizations_content = organizations_blob.download_as_string()
        df = pd.read_csv(io.StringIO(organizations_content.decode("utf-8")))

        #Lista de tipo de personal a extraer para cada entidad
        personales = ["Personal a Contrata", "Personal de Planta", "Personas naturales contratadas a honorarios"]
        results = []

        for index, row in df.iterrows():
            entidad = row["Entidad"]
            url = row["Enlace Portal"]
            
            if pd.isna(url):
                continue

            print(f"Procesando entidad: {entidad}")
            all_data = []  # Lista para almacenar los datos del año completo

            # Scraper principal
            for personal in personales:
                try:
                    # Seleccionar el tipo de personal
                    time.sleep(1)
                    elemento = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{personal}')]"))
                    )
                    elemento.click()
                    print(f"✔ Se hizo clic en {personal}")

                    # Capturar los años disponibles
                    table_two = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "tabTwo"))
                    )
                    years = table_two.find_elements(By.TAG_NAME, "li")
                    year_list = [year.text.strip() for year in years if year.text.strip().isdigit()]

                    for i, year in enumerate(year_list):
                        try:
                            time.sleep(1)

                            # Volver a capturar los años después de refrescar la página
                            table_two = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.ID, "tabTwo"))
                            )
                            anho = table_two.find_element(By.XPATH, f".//a[contains(text(), '{year}')]")
                            anho.click()
                            print(f"➡ Se hizo clic en el año: {year}")

                            # Capturar los meses disponibles
                            table_three = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.ID, "tabThree"))
                            )
                            months = table_three.find_elements(By.TAG_NAME, "li")
                            month_list = [month.text.strip() for month in months]

                            if not month_list:
                                print(f"⚠ No hay meses disponibles para el año {year}. Pasando al siguiente año...")
                                continue

                            for month in month_list:
                                try:
                                    time.sleep(1)
                                    mes = WebDriverWait(driver, 3).until(
                                        EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{month}')]"))
                                    ) 
                                    mes.click()
                                    print(f'✅ Se hizo clic en el mes: {month}')
                                    time.sleep(1)
                                    while True:
                                        # Encontrar la tabla
                                        tabla = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.XPATH, "//table"))
                                        )

                                        # Obtener nombres de las columnas desde thead
                                        columnas = [col.text.strip() for col in tabla.find_elements(By.XPATH, ".//thead/tr/th")]
                                        if not columnas:  # Si no hay columnas en thead, intentar en tbody
                                            columnas = [col.text.strip() for col in tabla.find_elements(By.XPATH, ".//tbody/tr[1]/td")]

                                        # Obtener los datos de la tabla usando JavaScript
                                        script = """
                                        let filas = document.querySelectorAll("table tbody tr");
                                        return Array.from(filas).map(fila => 
                                            Array.from(fila.querySelectorAll("td")).map(td => td.innerText.trim())
                                        );
                                        """
                                        datos_extraidos = driver.execute_script(script)

                                        # Agregar los datos a all_data
                                        for datos_fila in datos_extraidos:
                                            if len(datos_fila) == len(columnas):
                                                print('🔄️ Extrayendo datos de tabla...')
                                                datos_fila.append(personal)
                                                all_data.append(datos_fila)

                                        # Verificar si hay un botón "Siguiente" y si no está deshabilitado
                                        try:
                                            next_button = driver.find_element(By.CLASS_NAME, "ui-paginator-next")
                                            if "ui-state-disabled" in next_button.get_attribute("class"):
                                                print("⏹ Última página alcanzada.")
                                                break

                                            next_button.click()
                                            time.sleep(0.5)

                                        except:
                                            print("❌ No se encontró el botón 'Siguiente', terminando paginación.")
                                            break

                                except:
                                    print(f"⚠ Mes {month} no disponible.")
                                    if i == len(year_list) - 1:
                                        print(f"⚠ {year} era el último año. Pasando al siguiente tipo de personal...")
                                        driver.refresh()
                                        break
                                    else:
                                        print(f"⚠ Pasando al siguiente año...")
                                        break

                                # Recargar la página y volver a seleccionar personal y año
                                driver.refresh()
                                time.sleep(2)

                                # Volver a seleccionar el tipo de personal
                                elemento = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{personal}')]"))
                                )
                                elemento.click()
                                time.sleep(1)

                                # Volver a seleccionar el año
                                table_two = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.ID, "tabTwo"))
                                )
                                anho = table_two.find_element(By.XPATH, f".//a[contains(text(), '{year}')]")
                                anho.click()
                                time.sleep(1)

                            time.sleep(1)

                        except:
                            print(f"⚠ Error al hacer clic en el año {year}. Pasando al siguiente año...")
                            continue

                    time.sleep(2)

                except:
                    print(f"⚠ No se pudo hacer clic en {personal}. Pasando al siguiente tipo de personal...")
            
            # Guardar los datos en el bucket de GCS
            if all_data:
                max_columnas = max(len(fila) for fila in all_data)
                columnas = ["Column_" + str(i) for i in range(max_columnas)]
                df_export = pd.DataFrame(all_data, columns=columnas)
                
                # Carga a GCS
                filename = f"{entidad}_data.csv"
                gcs_path = upload_to_gcs(df_export, filename)
                results.append({
                    "entidad": entidad,
                    "status": "success",
                    "file_path": gcs_path
                })

        driver.quit()
        print("Scraping completado exitosamente!")
        print(f"Resultados: {results}")
        return results

    except Exception as e:
        print(f"Error durante el scraping: {str(e)}")
        raise e

# Función para ejecutar el scraping
def run_scraping():
    main()

if __name__ == "__main__":
    # Ejecutar el scraping en un hilo separado
    scraping_thread = threading.Thread(target=run_scraping)
    scraping_thread.start()
    
    # Iniciar el servidor Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
