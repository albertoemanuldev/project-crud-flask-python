import re


def validar_formato_cpf(cpf: str) -> bool:
    """
    Verifica se o CPF está no formato 000.000.000-00 usando Regex.
    Responsabilidade: apenas validar o formato, não o conteúdo.
    """
    padrao = r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"
    return re.match(padrao, cpf) is not None


def sanitizar_cpf(cpf: str) -> str:
    """
    Remove pontos e traço do CPF antes de salvar ou comparar.
    Ex: 123.456.789-09 → 12345678909
    """
    return re.sub(r"[.\-]", "", cpf)