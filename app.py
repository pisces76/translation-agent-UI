import gradio as gr
import re
from difflib import Differ
from src.translation_agent.utils import *

LANGUAGES = {
    'English': 'English',
    'Español': 'Spanish',
    'Français': 'French',
    'Deutsch': 'German',
    'Italiano': 'Italian',
    'Português': 'Portuguese',
    'Русский': 'Russian',
    '中文': 'Chinese',
    '日本語': 'Japanese',
    '한국어': 'Korean',
    'العربية': 'Arabic',
    'हिन्दी': 'Hindi',
}


def diff_texts(text1, text2, lang):
    d = Differ()
    ic(lang)
    if lang == '中文':
        return [
            (token[2:], token[0] if token[0] != " " else None)
            for token in d.compare(text1, text2)
            if token[0] in ["+", " "]
        ]
    else:
        words1 = re.findall(r'\S+|\s+', text1)
        words2 = re.findall(r'\S+|\s+', text2)

        return [
            (token[2:], token[0] if token[0] != " " else None)
            for token in d.compare(words1, words2)
            if token[0] in ["+", " "]
        ]
    

def translate_text(source_lang, target_lang, source_text, country, max_tokens=MAX_TOKENS_PER_CHUNK):
    num_tokens_in_text = num_tokens_in_string(source_text)

    ic(num_tokens_in_text)

    if num_tokens_in_text < max_tokens:
        ic("Translating text as single chunk")

        #Note: use yield from B() if put yield in function B()
        translation_1 = one_chunk_initial_translation(
            source_lang, target_lang, source_text
        )
        yield translation_1, None, None

        reflection = one_chunk_reflect_on_translation(
            source_lang, target_lang, source_text, translation_1, country
        )
        yield translation_1, reflection, None

        translation_2 = one_chunk_improve_translation(
            source_lang, target_lang, source_text, translation_1, reflection
        )
        translation_diff = diff_texts(translation_1, translation_2, target_lang)
        yield translation_1, reflection, translation_diff

    else:
        ic("Translating text as multiple chunks")

        token_size = calculate_chunk_size(
            token_count=num_tokens_in_text, token_limit=max_tokens
        )

        ic(token_size)

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name = "gpt-4",
            chunk_size=token_size,
            chunk_overlap=0,
        )

        source_text_chunks = text_splitter.split_text(source_text)
        
        translation_1_chunks = multichunk_initial_translation(
            source_lang, target_lang, source_text_chunks
        )
        ic(translation_1_chunks)
        translation_1 = "".join(translation_1_chunks)
        yield translation_1, None, None

        reflection_chunks = multichunk_reflect_on_translation(
            source_lang,
            target_lang,
            source_text_chunks,
            translation_1_chunks,
            country,
        )
        ic(reflection_chunks)
        reflection = "".join(reflection_chunks)
        yield translation_1, reflection, None

        translation_2_chunks = multichunk_improve_translation(
            source_lang,
            target_lang,
            source_text_chunks,
            translation_1_chunks,
            reflection_chunks,
        )
        ic(translation_2_chunks)
        translation_2 = "".join(translation_2_chunks)
        translation_diff = diff_texts(translation_1, translation_2, target_lang)
        
        yield translation_1, reflection, translation_diff
        


def update_ui(translation_1, reflection, translation_diff):
    return gr.update(value=translation_1), gr.update(value=reflection), gr.update(value=translation_diff)

with gr.Blocks() as demo:
    gr.Markdown("# Andrew Ng's Translation Agent ")
    with gr.Row():
        source_lang = gr.Dropdown(choices=list(LANGUAGES.keys()), value='English', label="Source Language")
        target_lang = gr.Dropdown(choices=list(LANGUAGES.keys()), value='中文', label="Target Language")
        country = gr.Textbox(label="Country (for target language)")
    source_text = gr.Textbox(label="Source Text", lines=5, show_copy_button=True)

    btn = gr.Button("Translate")

    with gr.Row():
        translation_1 = gr.Textbox(label="Initial Translation", lines=3)
        reflection = gr.Textbox(label="Reflection", lines=3)

    translation_diff = gr.HighlightedText  (label="Final Translation",
                                            combine_adjacent=True,
                                            show_legend=True,
                                            color_map={"+": "red"})
    #translation = gr.Textbox(label="Final Translation", lines=5, show_copy_button=True)

    btn.click(translate_text, inputs=[source_lang, target_lang, source_text, country], outputs=[translation_1, reflection, translation_diff], queue=True)
    btn.click(update_ui, inputs=[translation_1, reflection, translation_diff], outputs=[translation_1, reflection, translation_diff], queue=True)

demo.launch()
