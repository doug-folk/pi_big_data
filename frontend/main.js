class GameFinder {
    constructor() {
        this.API_BASE_URL = "http://127.0.0.1:8000/api";
        this.currentGames = [];
        this.init();
    }

    isValidExternalUrl(url) {
        if (!url || typeof url !== "string") return false;
        const trimmed = url.trim();
        if (!trimmed || trimmed.toLowerCase() === "unknown") return false;
        return /^https?:\/\//i.test(trimmed);
    }

    init() {
        this.bindEvents();
        this.loadFiltersData();
        this.loadInitialGames();
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(e.target.dataset.section);
            });
        });

        // Search
        document.getElementById('search-button').addEventListener('click', () => {
            this.performSearch();
        });

        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // Quick actions
        document.getElementById('random-games-btn').addEventListener('click', () => {
            this.loadRandomGames();
        });

        // Filters
        document.getElementById('apply-filters-btn').addEventListener('click', () => {
            this.applyFilters();
        });

        // Mood buttons
        const moodContainer = document.querySelector('.mood-buttons'); // container que envolve os botões
        if (moodContainer) {
            moodContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.mood-btn');
        if (!btn) return; // clicou fora do botão
        const mood = btn.dataset.mood;
        console.log('[GameFinder] botão mood clicado:', mood, btn);

        if (mood) {
            window.gameFinder.getRecommendationsByMood(mood);
        } else {
            console.warn('[GameFinder] dataset.mood não definido no botão', btn);
        }
            });
        } else {
            console.warn('[GameFinder] container .mood-buttons não encontrado');
        }

        // Similar games
        document.getElementById('find-similar-btn').addEventListener('click', () => {
            this.findSimilarGames();
        });

        // Modal
        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('game-modal').addEventListener('click', (e) => {
            if (e.target.id === 'game-modal') {
                this.closeModal();
            }
        });

        // Discover by Cluster
document.getElementById('find-cluster-btn').addEventListener('click', async () => {
    const gameName = document.getElementById('game-search-input').value.trim();
    if (!gameName) {
        alert("Digite o nome de um jogo!");
        return;
    }

    try {
        const searchUrl = `${this.API_BASE_URL}/games/search?q=${encodeURIComponent(gameName)}`;
        const searchResponse = await fetch(searchUrl);
        const searchData = await searchResponse.json();

        const gamesArray = Array.isArray(searchData.data) ? searchData.data
            : (searchData.data && Array.isArray(searchData.data.data)) ? searchData.data.data
            : [];

            if (gamesArray.length > 0) {
                const gameId = gamesArray[0].id;
                await this.discoverByCluster(gameId);
            } else {
                this.showError('Jogo não encontrado. Tente outro nome.');
            }
        } catch (error) {
            this.showError('Erro ao descobrir jogos pelo cluster.');
        }
    });

    }

    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Update sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${sectionName}-section`).classList.add('active');

        // Load section-specific content
        if (sectionName === 'discover') {
            this.loadDiscoverContent();
        } else if (sectionName === 'recommendations') {
            this.loadRecommendationsContent();
        }
    }

    async performSearch() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) return;

        this.showLoading();
        try {
            const url = `${this.API_BASE_URL}/games/search?q=${encodeURIComponent(query)}`;
            await this.fetchAndDisplayGames(url);
        } catch (error) {
            this.showError('Erro ao buscar jogos. Tente novamente.');
        }
    }

    async loadInitialGames() {
        this.showLoading();
        try {
            await this.fetchAndDisplayGames(`${this.API_BASE_URL}/games/discover`);
        } catch (error) {
            this.showError('Erro ao carregar jogos iniciais.');
        }
    }

    async loadRandomGames() {
        this.showLoading();
        try {
            await this.fetchAndDisplayGames(`${this.API_BASE_URL}/games/discover/random?n=12`);
        } catch (error) {
            this.showError('Erro ao carregar jogos aleatórios.');
        }
    }

    async applyFilters() {
        const genre = document.getElementById('genre-filter').value;
        const category = document.getElementById('category-filter').value;

        this.showLoading();
        try {
            const params = new URLSearchParams();
            if (genre) params.append('genre', genre);
            if (category) params.append('categoria', category);
            params.append('top_n', '20');

            const url = `${this.API_BASE_URL}/games/discover/by-filter?${params.toString()}`;
            await this.fetchAndDisplayGames(url);
        } catch (error) {
            this.showError('Erro ao aplicar filtros.');
        }
    }

    async getRecommendationsByMood(mood) {
        this.showLoading();
        try {
            const url = `${this.API_BASE_URL}/games/recommend/by-mood?mood=${encodeURIComponent(mood)}&top_n=12`;
            await this.fetchAndDisplayGames(url);
        } catch (error) {
            this.showError('Erro ao buscar recomendações por humor.');
        }
    }

    async findSimilarGames() {
        const gameName = document.getElementById('game-search-input').value.trim();
        if (!gameName) return;

        this.showLoading();
        try {
            const searchUrl = `${this.API_BASE_URL}/games/search?q=${encodeURIComponent(gameName)}`;
            const searchResponse = await fetch(searchUrl);
            const searchData = await searchResponse.json();

            // Corrigido: pega o array paginado corretamente
            const gamesArray = Array.isArray(searchData.data) ? searchData.data
                : (searchData.data && Array.isArray(searchData.data.data)) ? searchData.data.data
                : [];

            if (gamesArray.length > 0) {
                const gameId = gamesArray[0].id;
                const url = `${this.API_BASE_URL}/games/recommend/for-game/${gameId}?top_n=12`;
                await this.fetchAndDisplayGames(url);
            } else {
                this.showError('Jogo não encontrado. Tente outro nome.');
            }
        } catch (error) {
            this.showError('Erro ao buscar jogos similares.');
        }
    }

    async fetchAndDisplayGames(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            // Pega o array de jogos, seja paginado ou não
            let games = [];
            if (Array.isArray(data)) {
                games = data;
            } else if (Array.isArray(data.data)) {
                games = data.data;
            } else if (data.data && Array.isArray(data.data.data)) {
                games = data.data.data;
            }

            this.currentGames = games;
            this.displayGames(this.currentGames);
            this.hideLoading();
        } catch (error) {
            console.error('API error:', error);
            this.showError('Erro ao carregar jogos. Tente novamente.');
            this.hideLoading();
        }
    }

    useDemoData(url) {
        let games = [];
        
        if (url.includes('/search')) {
            const urlParams = new URLSearchParams(url.split('?')[1]);
            const query = urlParams.get('q') || '';
            const result = MOCK_API.search(query);
            games = result.data;
        } else if (url.includes('/by-mood')) {
            const urlParams = new URLSearchParams(url.split('?')[1]);
            const mood = urlParams.get('mood') || '';
            games = MOCK_API.byMood(mood);
        } else if (url.includes('/by-filter')) {
            const urlParams = new URLSearchParams(url.split('?')[1]);
            const genre = urlParams.get('genre') || '';
            const categoria = urlParams.get('categoria') || '';
            const result = MOCK_API.byFilter(genre, categoria);
            games = result.data;
        } else if (url.includes('/for-game/')) {
            const gameId = parseInt(url.match(/\/for-game\/(\d+)/)[1]);
            const result = MOCK_API.similar(gameId);
            games = result.data;
        } else if (url.includes('/random')) {
            const urlParams = new URLSearchParams(url.split('?')[1]);
            const n = parseInt(urlParams.get('n')) || 8;
            const result = MOCK_API.random(n);
            games = result.data;
        } else {
            // Default discover
            const result = MOCK_API.discover();
            games = result.data;
        }

        this.currentGames = games;
        this.displayGames(this.currentGames);
        this.hideLoading();
    }

    displayGames(games) {
        const gameList = document.getElementById('game-list');
        gameList.innerHTML = '';

        if (!games || games.length === 0) {
            gameList.innerHTML = '<div class="text-center"><p>Nenhum jogo encontrado.</p></div>';
            return;
        }

        games.forEach(game => {
            const gameCard = this.createGameCard(game);
            gameList.appendChild(gameCard);
        });
    }

    createGameCard(game) {
        const gameCard = document.createElement('div');
        gameCard.className = 'game-card';
        const hasValidUrl = this.isValidExternalUrl(game.url);

        if (hasValidUrl) {
            gameCard.onclick = () => window.open(game.url, "_blank");
            gameCard.style.cursor = 'pointer';
        } else {
            gameCard.onclick = null;
            gameCard.style.cursor = 'default';
            gameCard.classList.add('no-link');
        }

        let tags = [];
        if (Array.isArray(game.tags)) {
            tags = game.tags.slice(0, 3);
        } else if (typeof game.tags === "string") {
            tags = game.tags.split(',').map(t => t.trim()).slice(0, 3);
        }

        gameCard.innerHTML = `
            <div class="game-icon"><i class="fas fa-gamepad"></i></div>
            <div class="game-title">${game.title || game.name}</div>
            <div class="game-tags">
                ${tags.map(tag => `<span class="tag">${tag}</span>`).join("")}
            </div>
            ${hasValidUrl ? '' : '<div class="link-warning">Link indisponível</div>'}
        `;
        return gameCard;
    }

    showGameDetails(game) {
        const modal = document.getElementById('game-modal');
        const modalBody = document.getElementById('modal-body');

        const validImageUrl = this.isValidExternalUrl(game.image_url) ? game.image_url : null;
        const imageUrl = validImageUrl || 'https://via.placeholder.com/400x300?text=Sem+Imagem';
        const genre = game.genre || 'Não disponível';
        const categoria = game.categoria || 'Não disponível';
        const tags = Array.isArray(game.tags)
            ? game.tags
            : (typeof game.tags === "string" ? game.tags.split(',') : []);
        const cleanTags = tags
            .filter(Boolean)
            .map(tag => (typeof tag === "string" ? tag.trim() : tag))
            .slice(0, 6);
        const externalUrl = this.isValidExternalUrl(game.url) ? game.url : null;

        modalBody.innerHTML = `
            <h2>${game.title}</h2>
            <img src="${imageUrl}" alt="${game.title}" style="width: 100%; max-width: 400px; border-radius: 10px; margin: 1rem 0;" onerror="this.src='https://via.placeholder.com/400x300?text=Sem+Imagem'">
            <div class="game-details">
                <p><strong>Gênero:</strong> ${genre}</p>
                <p><strong>Categoria:</strong> ${categoria}</p>
                ${cleanTags.length > 0 ? `
                    <p><strong>Tags:</strong></p>
                    <div class="game-tags">
                        ${cleanTags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
                ${externalUrl ? `
                    <div style="margin-top: 2rem;">
                        <a href="${externalUrl}" target="_blank" class="action-btn" style="display: inline-block; text-decoration: none;">
                            <i class="fas fa-external-link-alt"></i>
                            Ver Jogo
                        </a>
                    </div>
                ` : `
                    <div class="link-warning" style="margin-top: 2rem;">
                        <i class="fas fa-ban"></i> Link externo indisponível
                    </div>
                `}
                <div style="margin-top: 1rem;">
                    <button class="action-btn" onclick="gameFinder.findSimilarGamesById(${game.id})">
                        <i class="fas fa-search-plus"></i>
                        Encontrar Similares
                    </button>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    async findSimilarGamesById(gameId) {
        this.closeModal();
        this.showLoading();
        try {
            const url = `${this.API_BASE_URL}/games/recommend/for-game/${gameId}?top_n=12`;
            await this.fetchAndDisplayGames(url);
        } catch (error) {
            this.showError('Erro ao buscar jogos similares.');
        }
    }

    closeModal() {
        document.getElementById('game-modal').classList.add('hidden');
    }

    showLoading() {
        document.getElementById('loading').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }

    showError(message) {
        const gameList = document.getElementById('game-list');
        gameList.innerHTML = `
            <div class="text-center" style="grid-column: 1 / -1; padding: 2rem; background: rgba(255, 255, 255, 0.9); border-radius: 15px; color: #000;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p style="font-size: 1.2rem; font-weight: 500;">${message}</p>
            </div>
        `;
        this.hideLoading();
    }

    loadDiscoverContent() {
        // Load preview games for discover section
        this.loadDiscoverPreview();
    }

    async loadDiscoverPreview() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/games/discover`);
            if (response.ok) {
                const data = await response.json();
                const games = (data.data || []).slice(0, 6); // Mostrar apenas 6 jogos
                this.displayDiscoverPreview(games);
            }
        } catch (error) {
            console.log('Erro ao carregar preview de jogos:', error);
            // Usar dados demo se disponível
            if (typeof MOCK_API !== 'undefined') {
                const result = MOCK_API.discover();
                this.displayDiscoverPreview(result.data.slice(0, 6));
            }
        }
    }

        async discoverByCluster(gameId) {
            this.showLoading();
                try {
                    const url = `${this.API_BASE_URL}/games/discover/by-cluster/${gameId}?top_n=12`;
                    await this.fetchAndDisplayGames(url);
                } catch (error) {
                    this.showError('Erro ao descobrir jogos pelo cluster.');
                }
        }


    displayDiscoverPreview(games) {
        const discoverGrid = document.getElementById('discover-games-grid');
        if (!discoverGrid) return;

        discoverGrid.innerHTML = '';

        games.forEach(game => {
            const gameCard = this.createSmallGameCard(game);
            discoverGrid.appendChild(gameCard);
        });
    }

    createSmallGameCard(game) {
        const gameCard = document.createElement('div');
        gameCard.className = 'game-card-small';
        const hasValidUrl = this.isValidExternalUrl(game.url);

        if (hasValidUrl) {
            gameCard.onclick = () => window.open(game.url, "_blank");
            gameCard.style.cursor = 'pointer';
        } else {
            gameCard.onclick = null;
            gameCard.style.cursor = 'default';
            gameCard.classList.add('no-link');
        }

        gameCard.innerHTML = `
            <div class="game-icon"><i class="fas fa-gamepad"></i></div>
            <div class="game-card-small-content">
                <h4>${game.title}</h4>
                <p>${game.genre || 'Gênero não disponível'}</p>
                ${hasValidUrl ? '' : '<span class="link-warning">Link indisponível</span>'}
            </div>
        `;

        return gameCard;
    }

    loadRecommendationsContent() {
        // Clear the game list when switching to recommendations
        document.getElementById('game-list').innerHTML = '';
    }

    async loadFiltersData() {
        try {
            // Carregar todos os jogos para extrair gêneros e categorias únicos
            const response = await fetch(`${this.API_BASE_URL}/games`);
            if (response.ok) {
                const data = await response.json();
                const games = data.data || [];
                
                this.populateFilters(games);
            }
        } catch (error) {
            console.log('Usando filtros padrão devido a erro na API:', error);
            // Manter filtros padrão se a API não estiver disponível
        }
    }

    populateFilters(games) {
        const genres = new Set();
        const categories = new Set();

        games.forEach(game => {
            if (game.genre) {
                game.genre.split(',').forEach(g => genres.add(g.trim()));
            }
            if (game.categoria) {
                if (Array.isArray(game.categoria)) {
                    game.categoria.forEach(c => categories.add(c.trim()));
                } else {
                    try {
                        let cats = JSON.parse(game.categoria);
                        if (Array.isArray(cats)) cats.forEach(c => categories.add(c.trim()));
                        else categories.add(game.categoria.trim());
                    } catch {
                        categories.add(game.categoria.trim());
                    }
                }
            }
        });

        // Atualizar select de gêneros
        const genreSelect = document.getElementById('genre-filter');
        genreSelect.innerHTML = '<option value="">Todos os gêneros</option>';
        Array.from(genres).sort().forEach(genre => {
            const option = document.createElement('option');
            option.value = genre;
            option.textContent = genre;
            genreSelect.appendChild(option);
        });

        // Atualizar select de categorias
        const categorySelect = document.getElementById('category-filter');
        categorySelect.innerHTML = '<option value="">Todas as categorias</option>';
        Array.from(categories).sort().forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categorySelect.appendChild(option);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.gameFinder = new GameFinder();
});
