from PIL import Image, ImageOps, ImageEnhance, ImageSequence
import numpy as np
import os
import multiprocessing
import time
import random
import string
import webbrowser
from colorama import init, Fore
import pyfiglet


init(autoreset=True)


DISCORD_LINK = "https://discord.gg/deinlinkhier"


def center_text(text):
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    return text.center(cols)

def print_welcome_message():
    ascii_art = """
 M   M   AAAAA  X   X  X   X 
 MM MM   A   A   X X    X X  
 M M M   AAAAA    X      X   
 M   M   A   A   X X    X X  
 M   M   A   A  X   X  X   X 

    """
    print(Fore.RED + ascii_art) 
    print(center_text(Fore.MAGENTA + "Tool for Change Color of logos(png and gif)"))
    print()
    print(center_text(Fore.WHITE + "Developer of this tool is: maxx.1337"))
    print()
    left_option = Fore.RED + "[1] > Color Change"
    right_option = Fore.YELLOW + "[2] > Support Server"
    print(center_text(left_option + " " * 20 + right_option))
    print()

def generate_random_folder(base_folder='output'):
    random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    folder_path = os.path.join(base_folder, random_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def change_hue(image, hue_shift):
    has_alpha = image.mode == 'RGBA'
    if has_alpha:
        image_rgb = image.convert('RGBA')
        r, g, b, a = image_rgb.split()
        image_rgb = Image.merge('RGB', (r, g, b))
    else:
        image_rgb = image.convert('RGB')
    image_hsv = image_rgb.convert('HSV')
    np_image = np.array(image_hsv).astype(int)
    np_image[..., 0] = (np_image[..., 0] + hue_shift) % 256
    modified_image_rgb = Image.fromarray(np.uint8(np_image), 'HSV').convert('RGB')
    if has_alpha:
        modified_image = Image.merge('RGBA', (*modified_image_rgb.split(), a))
    else:
        modified_image = modified_image_rgb
    return modified_image

def convert_to_grayscale(image):
    if image.mode == 'RGBA':
        r, g, b, a = image.split()
        grayscale_rgb = ImageOps.grayscale(Image.merge('RGB', (r, g, b))).convert('RGB')
        return Image.merge('RGBA', (*grayscale_rgb.split(), a))
    else:
        return ImageOps.grayscale(image)

def apply_saturation(image, output_folder, image_name, is_transparent):
    enhancer = ImageEnhance.Color(image)
    saturated_image = enhancer.enhance(2.0)
    subfolder = os.path.join(output_folder, 'saturated_transparent' if is_transparent else 'saturated_standard')
    os.makedirs(subfolder, exist_ok=True)
    saturated_path = os.path.join(subfolder, f'{image_name}_saturated.png')
    saturated_image.save(saturated_path, 'PNG')
    return saturated_path

def process_single_variation(args):
    image_path, output_folder, variation_index, num_variations, duration = args
    hue_shift = (variation_index * 256) // num_variations
    original_gif = Image.open(image_path)
    frames = [change_hue(frame.copy(), hue_shift) for frame in ImageSequence.Iterator(original_gif)]
    output_path = os.path.join(output_folder, f'gif_{variation_index+1}.gif')
    frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0, duration=duration)
    return output_path

def process_grayscale_gif(image_path, output_folder):
    original_gif = Image.open(image_path)
    duration = original_gif.info.get('duration', 100)
    grayscale_frames = [ImageOps.grayscale(frame.copy()) for frame in ImageSequence.Iterator(original_gif)]
    grayscale_gif_path = os.path.join(output_folder, 'grayscale.gif')
    grayscale_frames[0].save(grayscale_gif_path, save_all=True, append_images=grayscale_frames[1:], loop=0, duration=duration)
    return grayscale_gif_path

def process_gif(image_path, output_folder, num_variations=32):
    duration = Image.open(image_path).info.get('duration', 100)
    args_list = [(image_path, output_folder, i, num_variations, duration) for i in range(num_variations)]
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        saved_gifs = pool.map(process_single_variation, args_list)
    grayscale_gif = process_grayscale_gif(image_path, output_folder)
    return saved_gifs + [grayscale_gif]

def process_hue_shift(args):
    image_path, output_folder, hue_shift, index = args
    modified_image = change_hue(Image.open(image_path), hue_shift)
    output_path = os.path.join(output_folder, f'image_{index+1}.png')
    modified_image.save(output_path, 'PNG')
    image_name = f'image_{index+1}'
    is_transparent = modified_image.mode == 'RGBA'
    apply_saturation(modified_image, output_folder, image_name, is_transparent)
    return output_path

def generate_images(image_path, output_folder, num_variations=32):
    hue_shift_step = 256 // num_variations
    args_list = [(image_path, output_folder, i * hue_shift_step, i) for i in range(num_variations)]
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        saved_images = pool.map(process_hue_shift, args_list)
    return saved_images

def generate_grayscale(image_path, output_folder):
    grayscale_image = convert_to_grayscale(Image.open(image_path))
    grayscale_path = os.path.join(output_folder, 'grayscale.png')
    grayscale_image.save(grayscale_path, 'PNG')
    image_name = 'grayscale'
    is_transparent = grayscale_image.mode == 'RGBA'
    apply_saturation(grayscale_image, output_folder, image_name, is_transparent)
    return grayscale_path

def run_processing():
    logo = input('Gebe den Pfad vom Logo ein: ').strip()
    while True:
        num_variations = input('Gebe eine Anzahl an: ').strip()
        if not num_variations:
            num_variations = 32
            break
        try:
            num_variations = int(num_variations)
            break
        except ValueError:
            print('Bitte eine gültige Zahl eingeben!')

    start = time.time()
    output_folder = generate_random_folder()

    if logo.lower().endswith('.gif'):
        print('GIF erkannt, Verarbeitung läuft...')
        saved_gifs = process_gif(logo, output_folder, num_variations)
        print('Gespeicherte GIFs:')
        for gif_path in saved_gifs:
            print(gif_path)
    elif logo.lower().endswith('.png'):
        print('PNG erkannt, Verarbeitung läuft...')
        saved_images = generate_images(logo, output_folder, num_variations)
        grayscale = generate_grayscale(logo, output_folder)
        print(f'Graustufen-PNG gespeichert unter: {grayscale}')
        image = Image.open(logo)
        is_transparent = image.mode == 'RGBA'
        image_name = os.path.splitext(os.path.basename(logo))[0]
        saturated_path = apply_saturation(image, output_folder, image_name, is_transparent)
        print(f'Saturiertes Bild gespeichert unter: {saturated_path}')
    else:
        print('Dateityp nicht unterstützt. Bitte eine GIF oder PNG Datei angeben.')

    end = time.time()
    print(f'Bearbeitung abgeschlossen in {round(end - start)} Sekunden.')

def main():
    print_welcome_message()
    while True:
        choice = input(Fore.YELLOW + "] Choose : ").strip()
        if choice == '1':
            run_processing()
        elif choice == '2':
            print(Fore.GREEN + "Support Server wird im Browser geöffnet...")
            webbrowser.open(DISCORD_LINK)
            time.sleep(2)
        elif choice.lower() in ('exit', 'quit'):
            print(Fore.RED + "Programm wird beendet...")
            break
        else:
            print(Fore.RED + "Ungültige Eingabe, bitte erneut versuchen.")

if __name__ == '__main__':
    main()
