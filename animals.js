// 动物数据
const animals = [
    { name: '地包天', features: [0, 3, 5, 8, 10] },
    { name: '瓦力', features: [0, 4, 9] },
    { name: '莫斯', features: [0, 4, 9] },
    { name: '柯斯蒂', features: [0, 3, 5, 10] },
    { name: '暴莉', features: [0, 1] },
    { name: '咩咩', features: [0, 4, 5] },
    { name: '阿宝', features: [0, 1, 2, 3, 4, 5, 10] },
    { name: '阿瓜', features: [1, 3, 5, 9] },
    { name: '阿呆', features: [1, 3, 9] },
    { name: '优罗莎', features: [1, 9] },
    { name: '木木', features: [1, 3, 5, 8] },
    { name: '咕咕', features: [1, 3, 5, 9, 10] },
    { name: '鳄霸', features: [2, 3, 5, 8, 10] },
    { name: '瓦特', features: [2, 4] },
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
    { name: '奥里', features: [5, 10] },
    { name: '嘟嘟', features: [4, 5, 6, 8, 10] },
    { name: '奥姆诺姆', features: [5, 9] },
    { name: '玛奈奇', features: [4, 6, 8, 10] },
    { name: '苗苗', features: [4, 6, 8, 10] },
    { name: '星期天', features: [4, 6, 8, 10] },
    { name: '卡洛特', features: [4, 9] },
    { name: '培根', features: [9] },
    { name: '白菜狗', features: [7, 9] },
    { name: '小新', features: [9] },
    { name: '哈士企', features: [2, 5, 7, 8] },
    { name: '斯帕奇', features: [7, 8, 10] },
    { name: '珞珞', features: [4, 7, 8, 10] },
    { name: '桑尼', features: [4, 7, 8] },
    { name: '罗恩', features: [4, 7, 8] },
    { name: '斯黛拉', features: [4, 7, 8] },
    { name: '泰雷斯', features: [3] }
];

let selectedFeatures = [];

function toggleFeature(feature) {
    const index = selectedFeatures.indexOf(feature);
    if (index === -1) {
        selectedFeatures.push(feature); // 添加特征
    } else {
        selectedFeatures.splice(index, 1); // 移除特征
    }
    displayResults();
}

function displayResults() {
    const resultList = document.getElementById("resultList");
    resultList.innerHTML = ""; // 清空之前的结果

    const matches = animals.filter(animal => {
        return selectedFeatures.every(feature => animal.features.includes(feature));
    });

    if (matches.length === 0) {
        resultList.innerHTML = "<li>未找到匹配的动物</li>";
    } else {
        matches.forEach(animal => {
            const li = document.createElement("li");
            li.textContent = animal.name;
            resultList.appendChild(li);
        });
    }
}
