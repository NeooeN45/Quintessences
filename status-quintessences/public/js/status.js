const SERVICES = [
  {
    name: 'API GSIE',
    url: 'https://api.quintessences-platform.com/health',
    parser: async (response) => {
      const data = await response.json();
      return data && data.status === 'healthy';
    },
  },
  {
    name: 'Landing Page',
    url: 'https://quintessences-platform.com',
    parser: (response) => response.ok,
  },
  {
    name: 'Documentation OpenAPI',
    url: 'https://api.quintessences-platform.com/api/v1/openapi.json',
    parser: async (response) => {
      const data = await response.json();
      return data && data.openapi !== undefined;
    },
  },
];

const REFRESH_INTERVAL_MS = 60_000;

function createCard(service) {
  const card = document.createElement('div');
  card.className = 'service-card unknown';
  card.innerHTML = `<h3>${service.name}</h3><p class="service-status">Vérification…</p>`;
  return card;
}

async function checkService(service) {
  const response = await fetch(service.url, {
    method: 'GET',
    mode: 'cors',
    cache: 'no-store',
  });
  return service.parser(response);
}

async function updateCard(card, service) {
  try {
    const healthy = await checkService(service);
    card.className = `service-card ${healthy ? 'healthy' : 'unhealthy'}`;
    card.querySelector('.service-status').textContent = healthy
      ? 'Opérationnel'
      : 'Problème détecté';
    return healthy;
  } catch (err) {
    card.className = 'service-card unhealthy';
    card.querySelector('.service-status').textContent = `Indisponible (${err.message})`;
    return false;
  }
}

function setGlobalStatus(allHealthy) {
  const badge = document.getElementById('global-status');
  badge.className = `status-badge ${allHealthy ? 'healthy' : 'unhealthy'}`;
  badge.textContent = allHealthy
    ? 'Tous les services sont opérationnels'
    : 'Au moins un service est dégradé';
}

async function checkHealth() {
  const container = document.getElementById('services');
  container.innerHTML = '';
  setGlobalStatus(false);

  const results = await Promise.all(
    SERVICES.map(async (service) => {
      const card = createCard(service);
      container.appendChild(card);
      const healthy = await updateCard(card, service);
      return { service, healthy };
    })
  );

  const allHealthy = results.every((r) => r.healthy);
  setGlobalStatus(allHealthy);
  document.getElementById('last-check').textContent = new Date().toLocaleString('fr-FR');
}

document.getElementById('refresh').addEventListener('click', checkHealth);
checkHealth();
setInterval(checkHealth, REFRESH_INTERVAL_MS);
