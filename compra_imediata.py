import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import element_to_be_clickable, title_is
from time import sleep
import streamlit as st
import requests
import sys
from streamlit.web import cli as stcli
from streamlit import runtime
import os

def click(key):
    st.session_state['clicks'][key] = True

def unclick():
    st.session_state['clicks']['iniciarcompra'] = False
    st.session_state['clicks']['abrirnavegador'] = False

def main():


    if 'clicks' not in st.session_state:
        st.session_state['clicks'] = {}
    st.title('Auto compra')
    st.write("informe a url da compra, e informe a apikey para receber o callback no whatsapp")
    url = st.text_input("Informe a url de compra:")
    wpp_key = st.text_input("Informe a apikey whatsapp:")
    wpp_number = st.text_input("Informe a numero whatsapp:", placeholder="+5561********")
    if st.button("Testar msg whatsapp"):
        # Definindo a URL da API e os parâmetros
        url = "https://api.callmebot.com/whatsapp.php"
        params = {
            "phone": wpp_number,
            "text": "Funcionou :)",
            "apikey": wpp_key
        }
        # Enviando a requisição e recuperando a resposta
        response = requests.post(url, params=params)

        # Verificando o status da requisição
        if response.status_code == 200:
            # A requisição foi bem sucedida
            st.info("deu bom :)")
        else:
            # A requisição falhou
            st.info("Deu ruim, confere o numero ai")

    is_teste = st.checkbox("Rodar como teste, não irá clicar na compra.")

    # Definindo a URL
    #url = "https://comprei.pgfn.gov.br/anuncio/detalhe/7936"

    st.button("Abrir navegador", on_click=click, args=["abrirnavegador"])

    if st.session_state['clicks'].get("abrirnavegador", False) and url:
        st.write("Faça login no site de compra, depois clique em iniciar compra automática")
        # Abrindo o navegador e acessando a página
        if 'driver' not in st.session_state:
            st.session_state['driver'] = uc.Chrome()
        driver = st.session_state['driver']
        driver.get(url)

        st.button("Inicia compra automática", on_click=click, args=["iniciarcompra"])

        if st.session_state['clicks'].get("iniciarcompra", False):

            st.button("Parar compra automática", on_click=unclick)

            driver.implicitly_wait(1 * 10) # 1 minuto pra logar

            tempo_espera = 3 * 60  # 3 minutos em segundos

            espera_recado_wpp = time.time()
            # Criando um loop para verificar a clicabilidade do botão
            while True:
                try:

                    botao_compra_imediata = WebDriverWait(driver, 10).until(
                        element_to_be_clickable((By.XPATH, "//button[contains(text(),'Compra Imediata')]"))
                    )

                    # Se o botão for clicável, sair do loop
                    break
                except:
                    # Se o botão não for clicável, esperar mais tempo_espera
                    st.write("O botão 'Compra Imediata' não está clicável. Aguardando {} segundos...".format(tempo_espera))
                    driver.refresh()

                    if time.time() - espera_recado_wpp > (60 * 30) :
                        espera_recado_wpp = time.time()
                        send_msg_wpp(wpp_number, "O botão 'Compra Imediata' não está clicável. Aguardando {} segundos...".format(tempo_espera), wpp_key)

                    sleep(tempo_espera)


            st.write("clicando no botao de compra")
            botao_compra_imediata.click()


            st.write("Aguardando o redirecionamento para pagina de compra")
            WebDriverWait(driver, tempo_espera).until(
                title_is("COMPREI - Confirmação de Proposta")
            )

            # Esperando a página carregar
            driver.implicitly_wait(10)

            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

            st.write("Procurando checkbox de ciencia de compra")
            for checkbox in checkboxes:
                if checkbox.get_attribute("id") == "checkboxCiencia":
                    if not checkbox.is_selected():
                        label = driver.find_element(By.XPATH, "//div[@class='ciencia']/div[@class='br-checkbox']//label[@for='checkboxCiencia']")
                        label.click()
                        st.write("Clicamos no checkbox ciencia")

            st.write("Encontrando o botão 'Confirma Compra'")
            botao_confirma_compra = WebDriverWait(driver, 10).until(
                element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirma Compra')]"))
            )

            if botao_confirma_compra.is_enabled():
                ##https://api.callmebot.com/whatsapp.php?phone=+5561982633392&text="O botão 'Compra imediata' é clicável."&apikey=4153833

                msg_text = "Modo teste: O botão 'Compra imediata' é clicável."
                if is_teste:
                    st.write(msg_text)
                else:
                    send_msg_wpp(wpp_number, "clicando em compra", wpp_key)
                    msg_text = "Compra efetuada."
                    st.write(msg_text)
                    botao_confirma_compra.click()

                    botao_popup_sim = WebDriverWait(driver, 10).until(
                        element_to_be_clickable((By.XPATH, "//button[contains(text(),'Sim')]"))
                    )
                    botao_popup_sim.click()

                    st.balloons()

                send_msg_wpp(wpp_number, msg_text, wpp_key)

            else:
                st.write("O botão 'Compra imediata' não é clicável.")


def send_msg_wpp(wpp_number, msg_text, wpp_key):
    try:
        # Definindo a URL da API e os parâmetros
        url = "https://api.callmebot.com/whatsapp.php"
        params = {
            "phone": wpp_number,
            "text": msg_text,
            "apikey": wpp_key
        }

        # Enviando a requisição e recuperando a resposta
        response = requests.post(url, params=params)

        # Verificando o status da requisição
        if response.status_code == 200:
            # A requisição foi bem sucedida
            print("Mensagem enviada com sucesso!")
        else:
            # A requisição falhou
            st.write("Erro ao enviar mensagem:", response.status_code)
    except:
        st.write("Erro ao enviar mensagem")


if __name__ == '__main__':
    if runtime.exists():
        main()
    else:
        # Define a variável de ambiente
        compraimediatadir = os.getenv("compraimediatadir")

        # Completa o caminho do script
        script_path = os.path.join(compraimediatadir, "compra_imediata.py")

        # Executa o script
        sys.argv = ["streamlit", "run", script_path]
        sys.exit(stcli.main())