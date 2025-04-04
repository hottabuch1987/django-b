import re
import chardet
from django.shortcuts import render, redirect, get_object_or_404
from .models import Document, Chapter, Sentence
from .forms import DocumentUploadForm
from docx import Document as DocxDocument
import os
from django.shortcuts import render, redirect, get_object_or_404
from .models import Document, Chapter, Sentence
from .forms import DocumentUploadForm

from django.db.models import Q

def document_list(request):
    search_query = request.GET.get('q', '')
    document_filter = request.GET.get('document', '')
    
    # Основной запрос для документов
    documents = Document.objects.all().order_by('name')
    sentences = Sentence.objects.all()
    
    # Фильтрация
    if document_filter:
        sentences = sentences.filter(chapter__document_id=document_filter)
        documents = documents.filter(id=document_filter)
    
    if search_query:
        sentences = sentences.filter(text__icontains=search_query)

    # Определение шаблона для HTMX
    is_htmx = request.headers.get('HX-Request') == 'true'

    template = 'app/partials/search_results.html' if request.headers.get('HX-Request') else 'app/index.html'

    # Обработка формы загрузки
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                document = form.save()
                text = extract_text_from_file(document)
                structured_data = process_text(text)
                
                for chapter_data in structured_data:
                    chapter = Chapter.objects.create(
                        document=document,
                        number=chapter_data['chapter_number']
                    )
                    for i, sentence in enumerate(chapter_data['sentences'], start=1):
                        Sentence.objects.create(
                            chapter=chapter,
                            number=i,
                            text=sentence.strip()
                        )
                
                return redirect('document_list')
            
            except Exception as e:
                if document.id:
                    document.delete()
                return render(request, template, {
                    'form': form,
                    'error': str(e),
                    'documents': documents,
                    'all_documents': Document.objects.all(),
                    'sentences': sentences,
                    'search_query': search_query,
                    'document_filter': document_filter
                })
    else:
        form = DocumentUploadForm()

    return render(request, template, {
        'form': form,
        'documents': documents,
        'all_documents': Document.objects.all(),
        'sentences': sentences.select_related('chapter__document'),
        'search_query': search_query,
        'document_filter': document_filter
    })




def document_detail(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    chapters = document.chapters.all().prefetch_related('sentences').order_by('number')
    return render(request, 'app/document_detail.html', {
        'document': document,
        'chapters': chapters
    })

def extract_text_from_file(document):
    """Чтение содержимого файла (TXT или DOCX)"""
    if not document.file:
        raise ValueError("Файл не был загружен")

    file_path = document.file.path
    
    # Проверка существования файла
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    file_path = document.file.path

    if file_path.endswith('.txt'):
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected_encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            text = raw_data.decode(detected_encoding)
    elif file_path.endswith('.docx'):
        doc = DocxDocument(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Файл должен быть в формате .txt или .docx")

    return text



def process_text(text):
    """Разбивает текст на главы и предложения, исключая заголовки глав"""
    # Ищем все вхождения "Глава X" с различными вариантами
    chapter_pattern = re.compile(
        r'(?i)^Глава\s+(\d+)[.:]?\s*',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Разделяем текст на главы
    chapters = []
    last_pos = 0
    
    for match in chapter_pattern.finditer(text):
        chapter_number = int(match.group(1))
        start = match.end()  # Начинаем с позиции после заголовка главы
        
        # Добавляем предыдущую главу, если есть
        if chapters:
            chapters[-1]['end'] = match.start()
        
        chapters.append({
            'number': chapter_number,
            'start': start,
            'end': None
        })
        last_pos = match.end()
    
    # Обрабатываем последнюю главу
    if chapters:
        chapters[-1]['end'] = len(text)
    else:
        # Если нет ни одной главы, создаем главу 0
        chapters.append({
            'number': 0,
            'start': 0,
            'end': len(text)
        })
    
    # Извлекаем содержимое глав
    structured_data = []
    for chapter in chapters:
        if chapter['number'] == 0:
            continue  # Пропускаем неглавированные части
        
        content = text[chapter['start']:chapter['end']].strip()
        
        # Разделяем на предложения
        sentences = []
        current_sentence = []
        
        for part in re.split(r'([.!?…])', content):
            if part.strip():
                current_sentence.append(part.strip())
                if part in ['.', '!', '?', '…']:
                    sentence = ' '.join(current_sentence).strip()
                    if sentence:  # Игнорируем пустые предложения
                        sentences.append(sentence)
                    current_sentence = []
        
        # Добавляем последнее предложение, если осталось
        if current_sentence:
            sentence = ' '.join(current_sentence).strip()
            if sentence:
                sentences.append(sentence)
        
        if sentences:
            structured_data.append({
                'chapter_number': chapter['number'],
                'sentences': sentences
            })
    
    return structured_data