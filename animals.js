/* ---------- 特征映射 ---------- */
const featureNames = [
  '头上有角的动物','会飞的动物','会潜水的动物','会下蛋的动物','毛茸茸的动物',
  '眼睛大的动物','猫科动物','犬科动物','吃肉的动物','吃植物的动物','尾巴长的动物'
];

/* ---------- 动物数据 ---------- */
const animals = [
    { name: '地包天', features: [0, 3, 5, 8, 10] },
    { name: '瓦力', features: [0, 4, 9] },
    { name: '莫斯', features: [0, 4, 9] },
    { name: '柯蒂斯', features: [0, 3, 5, 9, 10] },
    { name: '暴莉', features: [0, 1] },
    { name: '咩咩', features: [0, 4, 5] },
    { name: '阿宝', features: [0, 1, 2, 3, 4, 5, 10] },
    { name: '阿瓜', features: [1, 2, 3, 5, 9] },
    { name: '阿呆', features: [1, 2, 3, 9] },
    { name: '优罗莎', features: [1, 9] },
    { name: '木木', features: [1, 3, 5, 8] },
    { name: '咕咕', features: [1, 3, 5, 9, 10] },
    { name: '鳄霸', features: [2, 3, 5, 8, 10] },
    { name: '瓦特', features: [2, 4, 8] },
    { name: '布鲁斯', features: [2, 3, 8, 10] },
    { name: '锤子', features: [2, 3, 8, 10] },
    { name: '图斯卡尔', features: [2, 8] },
    { name: '豆豆', features: [3, 5, 9] },
    { name: '尼莫', features: [4, 7, 8] },
    { name: '玛奇朵', features: [4, 6, 8, 10] },
    { name: '希子', features: [4, 6, 8, 10] },
    { name: '卡托', features: [4, 7, 8, 10] },
    { name: '泰哥', features: [4, 6, 8, 10] },
    { name: '芭比', features: [4, 9] },
    { name: '可乐', features: [4, 9] },
    { name: '刺头', features: [4, 8] },
    { name: '麦克斯', features: [4, 7, 8, 10] },
    { name: '福吉', features: [4, 9, 10] },
    { name: '利威尔', features: [4, 6, 8, 10] },
    { name: '高非', features: [4, 9] },
    { name: '八公', features: [4, 7, 8, 10] },
    { name: '加肥', features: [4, 6, 8, 10] },
    { name: '山姆', features: [4, 7, 8, 10] },
    { name: '毛毛', features: [4, 7, 8, 10] },
    { name: '雪诺', features: [4, 7, 8, 10] },
    { name: '宝伯', features: [4, 9] },
    { name: '福宝', features: [4, 9] },
    { name: '奥里', features: [2, 5, 9, 10] },
    { name: '嘟嘟', features: [4, 5, 6, 8, 10] },
    { name: '奥姆诺姆', features: [5, 9] },
    { name: '玛奈奇', features: [4, 6, 8, 10] },
    { name: '苗苗', features: [4, 6, 8, 10] },
    { name: '星期天', features: [4, 6, 8, 10] },
    { name: '卡洛特', features: [4, 9] },
    { name: '培根', features: [9] },
    { name: '白菜狗', features: [9] },
    { name: '小新', features: [9] },
    { name: '哈士企', features: [2, 4, 5, 7, 8] },
    { name: '斯帕奇', features: [7, 8, 10] },
    { name: '珞珞', features: [4, 7, 8, 10] },
    { name: '桑尼', features: [7, 8] },
    { name: '罗恩', features: [4, 7, 8] },
    { name: '斯黛拉', features: [4, 7, 8] },
    { name: '泰雷斯', features: [2, 3] },
    { name: '妙妙', features: [4, 6, 8, 10] },
    { name: '丘丘', features: [2, 3, 4, 8] },
    { name: '巴巴拉', features: [2, 4, 9] },
    { name: '糊涂', features: [1, 3, 5, 8] },
    { name: '坨坨', features: [4, 5, 9, 10] },
    { name: '瑞文', features: [1, 3, 4, 5, 8] },
    { name: '2662', features: [1, 2, 5] },
    { name: 'Vicksy', features: [4, 5, 7, 8, 10] },
    { name: '纳鲁', features: [9] }
];


/* ---------- 状态 ---------- */
let selectedFeatures = [];

/* ---------- 交互 ---------- */
function toggleFeature(index){
  const btn = document.querySelectorAll('.category-btn')[index];
  if(selectedFeatures.includes(index)){
    selectedFeatures = selectedFeatures.filter(i => i !== index);
    btn.classList.remove('selected');
  }else{
    selectedFeatures.push(index);
    btn.classList.add('selected');
  }
  displayResults();
}

function clearAll(){
  selectedFeatures = [];
  document.querySelectorAll('.category-btn').forEach(btn=>btn.classList.remove('selected'));
  displayResults();
}

/* ---------- 结果渲染 ---------- */
function displayResults(){
  const resultList  = document.getElementById('resultList');
  const summaryText = document.getElementById('summaryText');
  resultList.innerHTML = '';

  /* 1) 过滤匹配 */
  const matches = animals.filter(a =>
    selectedFeatures.every(f => a.features.includes(f))
  );

  /* 2) 渲染卡片或空状态 */
  if(matches.length){
    matches.forEach(a=>{
      const li   = document.createElement('li');  li.className = 'card';
      const img  = document.createElement('img'); img.src = `images/${a.name}.png`; img.alt = a.name; img.className = 'animal-avatar';
      const name = document.createElement('span'); name.textContent = a.name;
      li.append(img,name); resultList.appendChild(li);
    });
  }else{
    resultList.innerHTML = '<li>未找到匹配的动物</li>';
  }

  /* 3) 更新 summary 文案 —— 关键改动 */
  if(selectedFeatures.length){
    const tags = selectedFeatures.map(i => featureNames[i]).join('、');
    summaryText.textContent = `${tags}，共 ${matches.length} 个`;
  }else{
    summaryText.textContent = `所有动物，共 ${animals.length} 个`;
  }
}

/* ---------- 初始化 ---------- */
document.addEventListener('DOMContentLoaded', displayResults);