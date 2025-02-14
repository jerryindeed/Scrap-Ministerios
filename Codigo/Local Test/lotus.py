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

# Configuración de Selenium
chrome_options = Options()  
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")  # Asegurar tamaño correcto
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")


# Inicializar el servicio de ChromeDriver
service = Service(ChromeDriverManager().install())  


df = pd.read_csv("Datos/Listado_organizaciones_estado.csv")

# Lista de tipos de personal
personales = ["Personal a Contrata", "Personal de Planta", "Personas naturales contratadas a honorarios"]

for index, row in df.iterrows():
    entidad = row["Entidad"]
    url = row["Enlace Portal"]
    if pd.isna(url):
        continue  # Si la URL está vacía, saltar
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)  
    try: 
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        all_data = []  # Lista para almacenar los datos del año completo

        for personal in personales:
            try:
                # Seleccionar el tipo de personal
            
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
                        

                        # Volver a capturar los años después de refrescar la página
                        table_two = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "tabTwo"))
                        )
                        anho = table_two.find_element(By.XPATH, f".//a[contains(text(), '{year}')]")
                        anho.click()
                        print(f"➡ Se hizo clic en el año: {year}")
                        print("🔍 Extrayendo meses...")
                        time.sleep(5)

                        # Esperar a que los meses se carguen correctamente antes de capturarlos
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, "tabThree"))
                        )

                        # Recapturar la lista de meses después de cambiar de año
                        table_three = driver.find_element(By.ID, "tabThree")
                        months = WebDriverWait(table_three, 5).until(
                            EC.presence_of_all_elements_located((By.TAG_NAME, "li"))
                        )
                        month_list = [month.text.strip() for month in months if month.text.strip()]
                        
                        print(month_list)

                        if not month_list:
                            print(f"⚠ No se detectaron meses para el año {year}. Recargando la página y reintentando...")
                            driver.refresh()
                            
                            continue  # Pasar al siguiente año si no se detectan meses

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

                                    # Agregar los datos a all_data, asegurando que coincidan con las columnas
                                    for datos_fila in datos_extraidos:
                                        if len(datos_fila) == len(columnas):
                                            datos_fila.append(personal)
                                            all_data.append(datos_fila)

                                    # Verificar si hay un botón "Siguiente" y si no está deshabilitado
                                    try:
                                        next_button = driver.find_element(By.CLASS_NAME, "ui-paginator-next")
                                        if "ui-state-disabled" in next_button.get_attribute("class"):
                                            print("⏹ Última página alcanzada.")
                                            break  # Si el botón está deshabilitado, salir del bucle

                                        next_button.click()
                                        time.sleep(0.5)  # Esperar para cargar la siguiente página

                                    except:
                                        print("❌ No se encontró el botón 'Siguiente', terminando paginación.")
                                        break


                            except:
                                print(f"⚠ Mes {month} no disponible.")

                                # Si es el último año, pasa al siguiente personal
                                if i == len(year_list) - 1:
                                    print(f"⚠ {year} era el último año. Pasando al siguiente tipo de personal...")
                                    driver.refresh()
                                    break  # Sale del bucle de años

                                # Si no es el último año, pasa al siguiente año
                                else:
                                    print(f"⚠ Pasando al siguiente año...")
                                    break  # Sale del bucle de meses y va al siguiente año
                            # Recargar la página y volver a seleccionar personal y año antes de continuar
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
                        continue  # Si hay un error con el año, pasa al siguiente
                        
                

                time.sleep(2)

            except:
                print(f"⚠ No se pudo hacer clic en {personal}. Pasando al siguiente tipo de personal...")
    except Exception as e:
        print(f"❌ Error en la página {url}: {str(e)}")   
    driver.quit()
    # Guardar los datos en un solo CSV por entidad
    # Asegurar que todas las filas tengan el mismo número de columnas antes de crear el DataFrame
    max_columnas = max(len(fila) for fila in all_data) if all_data else 0

    if max_columnas > len(columnas):
        print(f"⚠ Hay más datos ({max_columnas}) que columnas definidas ({len(columnas)}). Ajustando...")
        columnas.extend([f"Extra_{i}" for i in range(max_columnas - len(columnas))]) 
        
    elif max_columnas < len(columnas):
        print(f"⚠ Hay menos datos ({max_columnas}) que columnas definidas ({len(columnas)}). Ajustando...")
        columnas = columnas[:max_columnas] 

    # Crear el DataFrame asegurando que las columnas coincidan con los datos
    df_export = pd.DataFrame(all_data, columns=columnas)

    # Guardar archivo
    file_path = f"Datos/{entidad}_data.csv"
    df_export.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"📂 Archivo guardado: {file_path}")
    print("➡ Siguiente URL")

print("✅ Proceso completado")
