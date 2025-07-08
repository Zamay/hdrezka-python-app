from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import traceback
from HdRezkaApi import HdRezkaApi

app = Flask(__name__)
CORS(app)

# HTML шаблон (вбудований в код)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HdRezka API Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h2 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        input, select, button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background: #4CAF50;
            color: white;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #45a049;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .result {
            background: #f9f9f9;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            white-space: pre-wrap;
            font-family: monospace;
            max-height: 400px;
            overflow-y: auto;
        }
        .error {
            background: #ffebee;
            border-color: #f44336;
            color: #d32f2f;
        }
        .success {
            background: #e8f5e8;
            border-color: #4CAF50;
            color: #2e7d32;
        }
        .loading {
            color: #ff9800;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        #seasonEpisodeControls {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎬 HdRezka API Tester</h2>
        
        <div class="form-group">
            <label for="url">URL сайту:</label>
            <input type="url" id="url" placeholder="https://hdrezka.ag/..." 
                   value="https://hdrezka.me/animation/adventures/31356-arifureta-silneyshiy-remeslennik-v-mire-tv-1-2019.html#t:111-s:1-e:3">
        </div>

        <button onclick="parseContent()">📥 Парсити контент</button>
        <div id="parseResult" class="result" style="display: none;"></div>
    </div>

    <div class="container" id="streamContainer" style="display: none;">
        <h2>🎥 Отримати стрім</h2>
        
        <div class="form-group">
            <label for="translation">Переклад:</label>
            <select id="translation"></select>
        </div>

        <div id="seasonEpisodeControls">
            <div class="form-group">
                <label for="season">Сезон:</label>
                <select id="season"></select>
            </div>

            <div class="form-group">
                <label for="episode">Серія:</label>
                <select id="episode"></select>
            </div>
        </div>

        <button onclick="getStream()">🎬 Отримати стрім</button>
        <div id="streamResult" class="result" style="display: none;"></div>
        
        <div id="videoContainer" style="display: none; margin-top: 20px;">
            <h3>📺 Відео плеєр</h3>
            <div class="form-group">
                <label for="qualitySelect">Якість відео:</label>
                <select id="qualitySelect" onchange="changeVideoQuality()"></select>
            </div>
            <video id="videoPlayer" controls style="width: 100%; max-width: 800px; height: auto;">
                Ваш браузер не підтримує відео
            </video>
            <div id="videoInfo" style="margin-top: 10px; font-size: 14px; color: #666;"></div>
        </div>
    </div>

    <script>
        const API_BASE = '/api';
        let currentData = null;
        let currentStreamData = null;

        const urlInput = document.getElementById('url');
        const parseResultDiv = document.getElementById('parseResult');
        const streamContainerDiv = document.getElementById('streamContainer');
        const translationSelect = document.getElementById('translation');
        const seasonSelect = document.getElementById('season');
        const episodeSelect = document.getElementById('episode');
        const streamResultDiv = document.getElementById('streamResult');
        const videoContainerDiv = document.getElementById('videoContainer');
        const qualitySelect = document.getElementById('qualitySelect');
        const videoPlayer = document.getElementById('videoPlayer');
        const videoInfoDiv = document.getElementById('videoInfo');
        const seasonEpisodeControls = document.getElementById('seasonEpisodeControls');

        function showResult(element, data, isError = false) {
            element.style.display = 'block';
            element.className = `result ${isError ? 'error' : 'success'}`;
            element.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
        }

        function showLoading(element, message = 'Завантаження...') {
            element.style.display = 'block';
            element.className = 'result loading';
            element.textContent = message;
        }

        async function parseContent() {
            const url = urlInput.value;
            if (!url) {
                alert('Введіть URL!');
                return;
            }

            showLoading(parseResultDiv, 'Парсинг контенту...');
            streamContainerDiv.style.display = 'none';
            videoContainerDiv.style.display = 'none';
            
            try {
                const response = await fetch(`${API_BASE}/parse`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Помилка сервера при парсингу');
                }

                currentData = data;
                showResult(parseResultDiv, data);
                
                fillTranslations(data.translations);

                if (data.type === 'video.tv_series') {
                    seasonEpisodeControls.style.display = 'block';
                    fillSeasonsAndEpisodes(data);
                } else {
                    seasonEpisodeControls.style.display = 'none';
                }
                
                streamContainerDiv.style.display = 'block';
                
            } catch (error) {
                showResult(parseResultDiv, `Помилка: ${error.message}`, true);
            }
        }

        function fillTranslations(translations) {
            translationSelect.innerHTML = '';
            for (const [name, id] of Object.entries(translations)) {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = name;
                translationSelect.appendChild(option);
            }
        }

        function fillSeasonsAndEpisodes(data) {
            seasonSelect.innerHTML = '';
            episodeSelect.innerHTML = '';

            const selectedTranslatorId = translationSelect.value;
            const translatorName = Object.keys(data.translations).find(key => data.translations[key] === selectedTranslatorId);
            
            if (translatorName && data.seasons && data.seasons[translatorName]) {
                const seasonsInfoForTranslator = data.seasons[translatorName];
                
                for (const [id, name] of Object.entries(seasonsInfoForTranslator.seasons)) {
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = name;
                    seasonSelect.appendChild(option);
                }
                
                if (Object.keys(seasonsInfoForTranslator.seasons).length > 0) {
                    const firstSeasonId = Object.keys(seasonsInfoForTranslator.seasons)[0];
                    fillEpisodes(firstSeasonId);
                }
            }
        }

        function fillEpisodes(seasonId) {
            episodeSelect.innerHTML = '';
            
            if (!currentData || !currentData.seasons) return;
            
            const selectedTranslatorId = translationSelect.value;
            const translatorName = Object.keys(currentData.translations).find(key => currentData.translations[key] === selectedTranslatorId);

            if (translatorName && currentData.seasons[translatorName] && 
                currentData.seasons[translatorName].episodes && 
                currentData.seasons[translatorName].episodes[seasonId]) {
                
                const episodes = currentData.seasons[translatorName].episodes[seasonId];
                for (const [id, name] of Object.entries(episodes)) {
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = name;
                    episodeSelect.appendChild(option);
                }
            }
        }

        translationSelect.addEventListener('change', function() {
            if (currentData && currentData.type === 'video.tv_series') {
                fillSeasonsAndEpisodes(currentData);
            }
        });

        seasonSelect.addEventListener('change', function() {
            fillEpisodes(this.value);
        });

        async function getStream() {
            const url = urlInput.value;
            const translation = translationSelect.value;
            let season = null;
            let episode = null;

            if (!url || !translation) {
                alert('Спочатку парсіть контент та виберіть переклад!');
                return;
            }

            if (currentData && currentData.type === 'video.tv_series') {
                season = seasonSelect.value;
                episode = episodeSelect.value;
                if (!season || !episode) {
                    alert('Для серіалу виберіть сезон і серію!');
                    return;
                }
            }

            showLoading(streamResultDiv, 'Отримання стріму...');
            videoContainerDiv.style.display = 'none';
            
            try {
                const requestData = { url, translation };
                if (season) requestData.season = season;
                if (episode) requestData.episode = episode;

                const response = await fetch(`${API_BASE}/stream`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Помилка сервера при отриманні стріму');
                }

                currentStreamData = data;
                showResult(streamResultDiv, data);
                
                if (data.videos && Object.keys(data.videos).length > 0) {
                    showVideoPlayer(data.videos);
                } else {
                    showResult(streamResultDiv, 'Не знайдено доступних відеопотоків.', true);
                }
                
            } catch (error) {
                showResult(streamResultDiv, `Помилка: ${error.message}`, true);
            }
        }

        function showVideoPlayer(videos) {
            const qualities = Object.keys(videos).sort((a, b) => {
                const aNum = parseInt(a);
                const bNum = parseInt(b);
                return bNum - aNum;
            });
            
            qualitySelect.innerHTML = '';
            qualities.forEach(quality => {
                const option = document.createElement('option');
                option.value = quality;
                option.textContent = quality;
                qualitySelect.appendChild(option);
            });
            
            if (qualities.length > 0) {
                const bestQuality = qualities[0];
                qualitySelect.value = bestQuality;
                videoPlayer.src = videos[bestQuality];
                videoPlayer.load();
                updateVideoInfo(bestQuality, videos[bestQuality]);
            }
            
            videoContainerDiv.style.display = 'block';
        }

        function changeVideoQuality() {
            const selectedQuality = qualitySelect.value;
            
            if (currentStreamData && currentStreamData.videos[selectedQuality]) {
                const currentTime = videoPlayer.currentTime;
                videoPlayer.src = currentStreamData.videos[selectedQuality];
                videoPlayer.load();
                videoPlayer.currentTime = currentTime;
                videoPlayer.play();
                updateVideoInfo(selectedQuality, currentStreamData.videos[selectedQuality]);
            }
        }

        function updateVideoInfo(quality, url) {
            const urlShort = url.length > 100 ? url.substring(0, 100) + '...' : url;
            
            let seasonEpisode = '';
            if (currentStreamData.season && currentStreamData.episode) {
                seasonEpisode = `Сезон ${currentStreamData.season}, Серія ${currentStreamData.episode} | `;
            }
            
            videoInfoDiv.innerHTML = `
                <strong>Якість:</strong> ${quality} | 
                ${seasonEpisode}
                <strong>URL:</strong> <a href="${url}" target="_blank" style="color: #4CAF50;">${urlShort}</a>
            `;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/parse', methods=['POST'])
def parse_content():
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL є обов\'язковим'}), 400
        
        # Створюємо екземпляр API
        rezka = HdRezkaApi(url)
        
        # Отримуємо базову інформацію
        result = {
            'name': rezka.name,
            'type': rezka.type,
            'id': rezka.id,
            'translations': rezka.getTranslations()
        }
        
        # Якщо це серіал, отримуємо сезони та епізоди
        if rezka.type == 'video.tv_series':
            result['seasons'] = rezka.getSeasons()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Помилка при парсингу: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream', methods=['POST'])
def get_stream():
    try:
        data = request.json
        url = data.get('url')
        translation = data.get('translation')
        season = data.get('season')
        episode = data.get('episode')
        
        if not url or not translation:
            return jsonify({'error': 'URL та переклад є обов\'язковими'}), 400
        
        # Створюємо екземпляр API
        rezka = HdRezkaApi(url)
        
        # Отримуємо стрім
        stream = rezka.getStream(season, episode, translation)
        
        # Перевіряємо, чи отримали ми дані
        if not stream or not hasattr(stream, 'videos'):
            return jsonify({'error': 'Не вдалося отримати стрім'}), 404
        
        result = {
            'videos': stream.videos,
            'season': stream.season,
            'episode': stream.episode
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Помилка при отриманні стріму: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)