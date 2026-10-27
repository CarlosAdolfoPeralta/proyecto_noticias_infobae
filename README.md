# Análisis de noticias de Infobae con PLN

Proyecto que arma un corpus de noticias en español a partir del feed RSS de Infobae
y compara distintas técnicas de procesamiento de lenguaje natural (PLN) sobre ese corpus.

## Pregunta

¿Qué se puede aprender de un corpus de noticias en español con técnicas de PLN, y cómo se
comparan esas técnicas entre sí?

## Qué hace el proyecto

1. **Obtención de datos:** un script descarga el feed RSS y acumula las notas en un CSV, sin duplicados.
2. **Preprocesamiento:** limpieza y lematización con spaCy, conservando las negaciones (`no`, `nunca`, `sin`...),
   que spaCy trata como stopwords.
3. **Predecir la edición del diario** (`america`, `espana`, `mexico`, `peru`, `colombia`) a partir del texto:
   TF-IDF contra embeddings, ambos con regresión logística y validación cruzada de 5 folds, con un control
   del largo de texto que lee cada método.
4. **Descubrir temas sin etiquetas:** KMeans y BERTopic sobre embeddings, y comparación entre ambos.
5. **Clasificar por tema sin entrenar** (zero-shot con embeddings), evaluado con la sección temática que
   aparece en la URL de algunas notas.

## Estructura del repositorio

```
proyecto_noticias_infobae/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   └── actualizar_corpus.py     # descarga el feed y acumula las notas en data/
├── notebooks/
│   └── analisis.ipynb           # análisis completo, explicado paso a paso
└── data/                        # el corpus no se incluye en el repositorio
```

## Cómo reproducirlo

Probado con Python 3.13.

1. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   python -m spacy download es_core_news_md
   ```

2. Construir el corpus ejecutando el script **varias veces por día durante varios días**:

   ```bash
   python src/actualizar_corpus.py
   ```

   El feed entrega solo las últimas ~100 notas por consulta, así que el corpus depende de cada cuánto se
   ejecute el script. En Windows se puede automatizar con el Programador de tareas (por ejemplo, cada 30 minutos).

3. Abrir `notebooks/analisis.ipynb` y ejecutarlo de arriba hacia abajo. Lee `data/noticias_infobae.csv`.

**Importante:** los resultados dependen del corpus. Con otras notas cambiarán los números, la cantidad de temas
de BERTopic y la numeración de los grupos de KMeans. El diccionario `nombres_km` del notebook (que le pone
nombre a cada grupo) se asignó a mano para `SEED=42` y para el corpus original, por lo que hay que revisarlo
si el corpus es distinto.

## Sobre los datos

El corpus contiene el texto completo de las notas, que tiene derechos de autor, por eso **no se incluye
en el repositorio**. Se reconstruye con el script. Antes de usarlo, conviene revisar los términos de uso del sitio.

Los resultados de este repositorio se obtuvieron con **2500 notas** (se descargaron 2503; se descartaron
3 sin texto) publicadas entre el **23 de octubre de 2026 (19:00 UTC)** y el **27 de octubre de 2026 (03:27 UTC)**,
es decir, unas 80 horas.

## Resultados

| Tarea | Método | Métrica | Resultado |
|---|---|---|---|
| Predecir la edición (5 clases, 1852 notas) | Baseline: siempre `america` | accuracy | 0.42 |
| | TF-IDF + regresión logística (nota completa) | F1 macro | 0.85 |
| | TF-IDF + regresión logística (primeras 90 palabras) | F1 macro | 0.79 |
| | Embeddings + regresión logística | F1 macro | 0.65 |
| Descubrir temas sin etiquetas (2500 notas) | KMeans | k elegido / silhouette | k=10 / 0.100 |
| | BERTopic | temas / notas sin tema | 24 / 271 (11%) |
| Clasificar por tema sin entrenar (7 clases, 312 notas) | Baseline: siempre `deportes` | accuracy | 0.20 |
| | Zero-shot con embeddings | accuracy / F1 macro | 0.67 / 0.65 |

Lo que se observó:

- **Edición:** TF-IDF supera a los embeddings por 14 puntos de F1 macro con texto de largo comparable
  (0.79 contra 0.65) y por 20 con la nota completa (0.85). La confusión principal es entre `america` y `espana`:
  203 de los 313 errores (65%).
- **Temas:** KMeans con k entre 8 y 12 da silhouette parecido (0.089 a 0.100). Con BERTopic, 16 de los 24 temas
  tienen al menos el 75% de sus notas en un único grupo de KMeans.
- **Clasificación por tema:** deportes y salud se clasifican mejor; tecnología y cultura pierden más de la mitad de
  sus notas. Los errores más grandes son tecnología → cultura (15 notas, sobre todo YouTube, videojuegos y contenido con IA)
  y cultura → crimen (9 notas, cuatro de ellas el mismo hecho).

## Limitaciones

- El corpus cubre unas 80 horas, por lo que varios temas corresponden a un único hecho publicado en varias notas
  (un grupo de KMeans de 193 notas trata casi solo del balotaje de Brasil). En la validación cruzada, notas sobre el
  mismo hecho pueden quedar repartidas entre entrenamiento y prueba, lo que puede inflar los resultados.
- El feed solo entrega las últimas notas: los períodos en que el script no se ejecutó quedan sin cubrir.
- Los hiperparámetros (`C`, `class_weight`, `k` de KMeans, `min_cluster_size` y `min_samples` de HDBSCAN)
  se eligieron mirando resultados sobre el mismo corpus, así que los números pueden ser algo optimistas.
- En BERTopic hubo que fijar `min_cluster_size` y `min_samples` explícitamente: con `min_cluster_size=10` salieron
  82 temas, y con `min_cluster_size=30` y `min_samples=5`, un solo tema reunía 514 notas. En una etapa anterior,
  con 683 notas, el valor por defecto de `min_samples` produjo solo 4 temas.
- Las etiquetas de la clasificación por tema vienen de la sección de la URL (criterio del medio, no anotación propia),
  cubren solo 312 notas, y la categoría `crimen` tiene apenas 21.
- KMeans, BERTopic y el zero-shot usan los mismos embeddings, que leen solo los primeros ~128 tokens de cada nota.
  La coincidencia entre ellos no es una validación independiente.
- La interpretación de los grupos se basó en pocos títulos por grupo y en palabras clave: es una lectura cualitativa,
  no una medición.

## Tecnologías

Python, requests, BeautifulSoup, pandas, scikit-learn, spaCy, sentence-transformers
(`paraphrase-multilingual-MiniLM-L12-v2`), UMAP, HDBSCAN y BERTopic.

## Posibles extensiones

- Acumular más días y evaluar con una separación temporal (entrenar con los primeros días, probar con los últimos).
- Anotar etiquetas propias, con un conjunto de prueba separado.
- Comparar el zero-shot con un modelo de inferencia (NLI) sobre las mismas 312 notas.
- Fine-tuning de un modelo en español para clasificar por tema.
- Reconocimiento de entidades (NER) para describir cada edición.
