// 等待DOM内容完全加载后执行脚本，避免全局作用域污染
document.addEventListener('DOMContentLoaded', () => {

  /* ---------- 数据源 (单一数据源) ---------- */
  const features = [
    '头上有角', '会飞', '会潜水', '会下蛋', '毛茸茸',
    '眼睛大', '猫科', '犬科', '吃肉', '吃植物', '尾巴长'
  ];

  const animals = [
    { name: '地包天', features: [0, 3, 5, 8, 10] }, { name: '瓦力', features: [0, 4, 9] },
    { name: '莫斯', features: [0, 4, 9] }, { name: '柯蒂斯', features: [0, 3, 5, 9, 10] },
    { name: '暴莉', features: [0, 1] }, { name: '咩咩', features: [0, 4, 5] },
    { name: '阿宝', features: [0, 1, 2, 3, 4, 5, 10] }, { name: '阿瓜', features: [1, 2, 3, 5, 9] },
    { name: '阿呆', features: [1, 2, 3, 9] }, { name: '优罗莎', features: [1, 9] },
    { name: '木木', features: [1, 3, 5, 8] }, { name: '咕咕', features: [1, 3, 5, 9, 10] },
    { name: '鳄霸', features: [2, 3, 5, 8, 10] }, { name: '瓦特', features: [2, 4, 8] },
    { name: '布鲁斯', features: [2, 3, 8, 10] }, { name: '锤子', features: [2, 3, 8, 10] },
    { name: '图斯卡尔', features: [2, 8] }, { name: '豆豆', features: [3, 5, 9] },
    { name: '尼莫', features: [4, 7, 8] }, { name: '玛奇朵', features: [4, 6, 8, 10] },
    { name: '希子', features: [4, 6, 8, 10] }, { name: '卡托', features: [4, 7, 8, 10] },
    { name: '泰哥', features: [4, 6, 8, 10] }, { name: '芭比', features: [4, 9] },
    { name: '可乐', features: [4, 9] }, { name: '刺头', features: [4, 8] },
    { name: '麦克斯', features: [4, 7, 8, 10] }, { name: '福吉', features: [4, 9, 10] },
    { name: '利威尔', features: [4, 6, 8, 10] }, { name: '高非', features: [4, 9] },
    { name: '八公', features: [4, 7, 8, 10] }, { name: '加肥', features: [4, 6, 8, 10] },
    { name: '山姆', features: [4, 7, 8, 10] }, { name: '毛毛', features: [4, 7, 8, 10] },
    { name: '雪诺', features: [4, 7, 8, 10] }, { name: '宝伯', features: [4, 9] },
    { name: '福宝', features: [4, 9] }, { name: '奥里', features: [2, 5, 9, 10] },
    { name: '嘟嘟', features: [4, 5, 6, 8, 10] }, { name: '奥姆诺姆', features: [5, 9] },
    { name: '玛奈奇', features: [4, 6, 8, 10] }, { name: '苗苗', features: [4, 6, 8, 10] },
    { name: '星期天', features: [4, 6, 8, 10] }, { name: '卡洛特', features: [4, 9] },
    { name: '培根', features: [9] }, { name: '白菜狗', features: [9] },
    { name: '小新', features: [9] }, { name: '哈士企', features: [2, 4, 5, 7, 8] },
    { name: '斯帕奇', features: [7, 8, 10] }, { name: '珞珞', features: [4, 7, 8, 10] },
    { name: '桑尼', features: [7, 8] }, { name: '罗恩', features: [4, 7, 8] },
    { name: '斯黛拉', features: [4, 7, 8] }, { name: '泰雷斯', features: [2, 3] },
    { name: '妙妙', features: [4, 6, 8, 10] }, { name: '丘丘', features: [2, 3, 4, 8] },
    { name: '巴巴拉', features: [2, 4, 9] }, { name: '糊涂', features: [1, 3, 5, 8] },
    { name: '坨坨', features: [4, 5, 9, 10] }, { name: '瑞文', features: [1, 3, 4, 5, 8] },
    { name: '2662', features: [1, 2, 5] }, { name: 'Vicksy', features: [4, 5, 7, 8, 10] },
    { name: '纳鲁', features: [9] }
  ];

  /* ---------- DOM 元素缓存 ---------- */
  const categoryButtonsContainer = document.getElementById('categoryButtons');
  const resultList = document.getElementById('resultList');
  const summaryText = document.getElementById('summaryText');
  const clearButton = document.getElementById('clearButton');
  
  /* ---------- 状态 ---------- */
  let selectedFeatures = new Set(); // 使用 Set 数据结构，增删和检查存在性更高效

  /* ---------- 函数 ---------- */

  /**
   * 更新“一键清空”按钮的禁用状态和样式
   */
  const updateClearButtonState = () => {
    clearButton.disabled = selectedFeatures.size === 0;
  };

  /**
   * 渲染结果列表和摘要信息
   */
  const displayResults = () => {
    // 1) 过滤匹配的动物
    const matches = animals.filter(animal =>
      [...selectedFeatures].every(featureIndex => animal.features.includes(featureIndex))
    );

    // 2) 清空当前结果
    resultList.innerHTML = '';

    // 3) 渲染卡片或空状态
    if (matches.length > 0) {
      const fragment = document.createDocumentFragment(); // 使用文档片段提升性能
      matches.forEach(animal => {
        const li = document.createElement('li');
        li.className = 'card';
        
        const img = document.createElement('img');
        img.src = `images/${animal.name}.png`;
        img.alt = animal.name;
        img.className = 'animal-avatar';
        img.loading = 'lazy'; // 图片懒加载，提升初始加载性能
        
        const name = document.createElement('span');
        name.textContent = animal.name;
        
        li.append(img, name);
        fragment.appendChild(li);
      });
      resultList.appendChild(fragment);
    } else {
      const li = document.createElement('li');
      li.textContent = '未找到匹配的动物';
      resultList.appendChild(li);
    }

    // 4) 更新摘要文本
    if (selectedFeatures.size > 0) {
      const tags = [...selectedFeatures].map(i => features[i] + '的动物').join('、');
      summaryText.textContent = `${tags}，共 ${matches.length} 个`;
    } else {
      summaryText.textContent = `所有动物，共 ${animals.length} 个`;
    }

    // 5) 更新清空按钮状态
    updateClearButtonState();
  };

  /**
   * 处理特征按钮的点击事件
   * @param {number} index - 被点击按钮对应的特征索引
   * @param {HTMLElement} buttonElement - 被点击的按钮元素
   */
  const toggleFeature = (index, buttonElement) => {
    const isSelected = buttonElement.classList.toggle('selected');
    buttonElement.setAttribute('aria-pressed', isSelected); // 更新无障碍状态

    if (isSelected) {
      selectedFeatures.add(index);
    } else {
      selectedFeatures.delete(index);
    }

    displayResults();
  };

  /**
   * 清空所有选中的特征
   */
  const clearAll = () => {
    selectedFeatures.clear();
    // 移除所有按钮的选中状态
    document.querySelectorAll('.category-btn.selected').forEach(btn => {
      btn.classList.remove('selected');
      btn.setAttribute('aria-pressed', 'false');
    });
    displayResults();
  };

  /**
   * 初始化函数
   */
  const init = () => {
    // 动态生成特征按钮
    const buttonsFragment = document.createDocumentFragment();
    features.forEach((feature, index) => {
      const button = document.createElement('button');
      button.className = 'category-btn';
      button.textContent = feature;
      button.dataset.featureIndex = index; // 使用 data-* 属性存储索引
      button.setAttribute('aria-pressed', 'false'); // 初始无障碍状态
      buttonsFragment.appendChild(button);
    });
    categoryButtonsContainer.appendChild(buttonsFragment);

    // 设置事件监听器
    // 使用事件委托处理特征按钮点击
    categoryButtonsContainer.addEventListener('click', (event) => {
      const clickedButton = event.target.closest('.category-btn');
      if (clickedButton) {
        const featureIndex = parseInt(clickedButton.dataset.featureIndex, 10);
        toggleFeature(featureIndex, clickedButton);
      }
    });

    clearButton.addEventListener('click', clearAll);

    // 初始渲染
    displayResults();
  };

  /* ---------- 初始化 ---------- */
  init();
});