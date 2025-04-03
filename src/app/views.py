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
    """Разбивает текст на главы и предложения"""
    chapter_splits = re.split(r'\bГлава\s*(\d+)\b', text, flags=re.IGNORECASE)
    
    structured_data = []
    for i in range(1, len(chapter_splits), 2):
        chapter_number = chapter_splits[i].strip()
        chapter_content = chapter_splits[i + 1].strip() if i + 1 < len(chapter_splits) else ""

        if not chapter_number.isdigit():
            continue

        chapter_number = int(chapter_number)
        sentences = [s.strip() for s in re.split(r'\.\s*', chapter_content) if s.strip()]

        structured_data.append({
            'chapter_number': chapter_number,
            'sentences': sentences
        })

    return structured_data


