document.addEventListener('DOMContentLoaded', () => {
  const siteData = window.PARTY_ANIMALS_SITE_DATA || {};
  const pageKey = document.body?.dataset.page;

  const pages = {
    '动物特征分类': {
      data: siteData.animals,
      filterType: 'multi',
      itemType: '动物',
      summaryLabel: '特征',
      emptyText: '未找到匹配的动物',
      renderItem: renderAnimal,
      normalizeItem: normalizeAnimal,
    },
    '成就地图分类': {
      data: siteData.achievements,
      filterType: 'single',
      itemType: '成就',
      summaryLabel: '地图',
      emptyText: '未找到匹配的成就',
      renderItem: renderAchievement,
      normalizeItem: normalizeAchievement,
    },
  };

  const page = pages[pageKey];
  const categoryButtons = document.getElementById('categoryButtons');
  const resultList = document.getElementById('resultList');
  const summaryText = document.getElementById('summaryText');
  const clearButton = document.getElementById('clearButton');

  if (!page || !page.data || !categoryButtons || !resultList || !summaryText || !clearButton) {
    console.error('Page data or required DOM node is missing:', pageKey);
    return;
  }

  const features = page.data.features || [];
  const featureIndexById = new Map(features.map((feature, index) => [feature.id, index]));
  const items = (page.data.items || []).map(item => page.normalizeItem(item, featureIndexById));
  const selected = new Set();

  renderFilters();
  renderResults();

  categoryButtons.addEventListener('click', event => {
    const button = event.target.closest('.category-btn');
    if (!button) return;
    toggleFilter(Number(button.dataset.featureIndex), button);
  });

  clearButton.addEventListener('click', clearFilters);

  function renderFilters() {
    const fragment = document.createDocumentFragment();
    features.forEach((feature, index) => {
      const button = document.createElement('button');
      button.className = 'category-btn';
      button.type = 'button';
      button.textContent = feature.name;
      button.dataset.featureIndex = String(index);
      button.setAttribute('aria-pressed', 'false');
      fragment.appendChild(button);
    });
    categoryButtons.replaceChildren(fragment);
  }

  function toggleFilter(index, button) {
    const wasSelected = selected.has(index);

    if (page.filterType === 'single') {
      selected.clear();
      categoryButtons.querySelectorAll('.category-btn.selected').forEach(item => {
        item.classList.remove('selected');
        item.setAttribute('aria-pressed', 'false');
      });
      if (!wasSelected) selected.add(index);
    } else if (wasSelected) {
      selected.delete(index);
    } else {
      selected.add(index);
    }

    button.classList.toggle('selected', selected.has(index));
    button.setAttribute('aria-pressed', selected.has(index) ? 'true' : 'false');
    renderResults();
  }

  function clearFilters() {
    selected.clear();
    categoryButtons.querySelectorAll('.category-btn.selected').forEach(button => {
      button.classList.remove('selected');
      button.setAttribute('aria-pressed', 'false');
    });
    renderResults();
  }

  function renderResults() {
    const matches = selected.size === 0
      ? items
      : items.filter(item => [...selected].every(index => item.features.includes(index)));

    if (matches.length === 0) {
      const empty = document.createElement('li');
      empty.textContent = page.emptyText;
      resultList.replaceChildren(empty);
    } else {
      const fragment = document.createDocumentFragment();
      matches.forEach(item => fragment.appendChild(page.renderItem(item)));
      resultList.replaceChildren(fragment);
    }

    clearButton.disabled = selected.size === 0;
    summaryText.textContent = selected.size === 0
      ? `所有${page.itemType}，共 ${items.length} 个`
      : `拥有“${[...selected].map(index => features[index]?.name).join('、')}”${page.summaryLabel}的${page.itemType}，共 ${matches.length} 个`;
  }
});

function normalizeAnimal(animal, featureIndexById) {
  return {
    ...animal,
    features: (animal.featureIds || [])
      .map(featureId => featureIndexById.get(featureId))
      .filter(index => index !== undefined),
  };
}

function normalizeAchievement(achievement) {
  return achievement;
}

function renderAnimal(animal) {
  const card = document.createElement('li');
  card.className = 'card';

  const image = document.createElement('img');
  image.className = 'animal-avatar';
  image.src = animal.image;
  image.alt = animal.name;
  image.loading = 'lazy';

  const name = document.createElement('span');
  name.textContent = animal.name;

  card.append(image, name);
  return card;
}

function renderAchievement(achievement) {
  const card = document.createElement('li');
  card.className = 'card';

  const image = document.createElement('img');
  image.className = 'animal-avatar';
  image.src = achievement.image;
  image.alt = achievement.name;
  image.loading = 'lazy';
  image.onerror = () => {
    image.style.display = 'none';
  };

  const title = document.createElement('span');
  title.textContent = achievement.name;

  const condition = document.createElement('small');
  condition.textContent = achievement.condition || '（无完成条件）';

  card.append(image, title, condition);
  return card;
}
