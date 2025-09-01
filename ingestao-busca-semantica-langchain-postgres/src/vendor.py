import os

def select_vendor():
    options = ['google', 'openai']
    vendor = os.getenv('MODEL_VENDOR')
    if vendor in options:
        return vendor
    input_message = "Selecione o fornecedor:\n"
    for index, item in enumerate(options):
        input_message += f'{index+1}) {item}\n'
    
    vendor = None
    while vendor is None:
        choice = input(input_message)
        vendor = get_vendor_by_choice(choice, options)
    print(f"Fornecedor selecionado: {vendor}")        
    os.environ['MODEL_VENDOR'] = 'google'
    return vendor

def get_vendor_by_choice(choice, options):
    if is_number(choice):
        index = int(choice) - 1
        if index >= 0 and index < len(options):
            return options[index]
    print("Fornecedor inválido")
    return None


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
 
    
    