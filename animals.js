// 动物数据
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
    { name: '奥里', features: [2, 5, 10] },
    { name: '嘟嘟', features: [4, 5, 6, 8, 10] },
    { name: '奥姆诺姆', features: [5, 9] },
    { name: '玛奈奇', features: [4, 6, 8, 10] },
    { name: '苗苗', features: [4, 6, 8, 10] },
    { name: '星期天', features: [4, 6, 8, 10] },
    { name: '卡洛特', features: [4, 9] },
    { name: '培根', features: [9] },
    { name: '白菜狗', features: [7, 9] },
    { name: '小新', features: [9] },
    { name: '哈士企', features: [2, 4, 5, 7, 8] },
    { name: '斯帕奇', features: [7, 8, 10] },
    { name: '珞珞', features: [4, 7, 8, 10] },
    { name: '桑尼', features: [4, 7, 8] },
    { name: '罗恩', features: [4, 7, 8] },
    { name: '斯黛拉', features: [4, 7, 8] },
    { name: '泰雷斯', features: [3] },
    { name: '妙妙', features: [6, 4, 8, 10] },
    { name: '扣扣', features: [2, 8, 3] },
    { name: '巴巴拉', features: [2, 4, 9] },
    { name: '糊涂', features: [1, 5, 8, 3] },
    { name: '坨坨', features: [4, 9] },
    { name: '瑞文', features: [1, 3, 5, 9, 10] }
];

let selectedFeatures = [];

function toggleFeature(feature) {
    const index = selectedFeatures.indexOf(feature);
    const button = document.querySelector(`.category-btn[onclick="toggleFeature(${feature})"]`); // 获取当前按钮

    if (index === -1) {
        selectedFeatures.push(feature); // 添加特征
        button.classList.add("selected"); // 添加选中样式
    } else {
        selectedFeatures.splice(index, 1); // 移除特征
        button.classList.remove("selected"); // 移除选中样式
    }

    displayResults();
}

function displayResults() {
    const resultList = document.getElementById("resultList");
    resultList.innerHTML = "";

    const matches = animals.filter(animal => {
        return selectedFeatures.every(feature => animal.features.includes(feature));
    });

    if (matches.length === 0) {
        resultList.innerHTML = "<li>未找到匹配的动物</li>";
    } else {
        matches.forEach((animal, index) => {
            const li = document.createElement("li");
            
            // 创建头像
            const avatar = document.createElement("img");
            avatar.src = `images/${animal.name}.png`;  // 使用动物名字作为头像文件名
            avatar.alt = `${animal.name} 的头像`;
              avatar.classList.add("animal-avatar");

            // 创建名字
            const name = document.createElement("span");
            name.textContent = animal.name;

            li.appendChild(avatar);
            li.appendChild(name);
            resultList.appendChild(li);
        });
    }
}
