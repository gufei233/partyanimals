document.addEventListener('DOMContentLoaded', () => {

  // --- 数据源 ---
  const dataSources = {
    animals: {
      features: [
        '头上有角', '会飞', '会潜水', '会下蛋', '毛茸茸',
        '眼睛大', '猫科', '犬科', '吃肉', '吃植物', '尾巴长'
      ],
      items: [
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
      ]
    },
    achievements: {
      features: [
        '猛兽冰球','荒野大膘客','实验室','黑洞实验室','风洞',
        '猛兽电击球','荒岛','猛兽足球','棒棒糖工厂','进入游戏',
        '鳄霸谷','猛兽潜艇','猛兽橄榄球','炸弹投石机','碎裂浮冰',
        '暴风雪','加肥擂台','断桥','武道会','断箭行动',
        '黑帆','上海','矿山夺宝','其他'
      ],
      items: [
          { name: '完美格挡', condition: '在「猛兽冰球」用盾弹反冰球 3 次（快速游戏）', features: [0] },
          { name: '西部点子王', condition: '在「荒野大膘客」己方全部被淘汰（快速游戏）', features: [1] },
          { name: '我开悟了', condition: '在「实验室」的黑方碑房间对着立牌站 5 秒钟', features: [2] },
          { name: '知识渊博', condition: '在「实验室」的四位大科学家画像前得知他们的名字', features: [2] },
          { name: '风狗', condition: '在「风洞」赢得 5 局快速游戏经典模式', features: [4] },
          { name: '脑子瓦特', condition: '在「猛兽电击球」一局游戏内触发电击球爆炸 10 次（快速游戏）', features: [5] },
          { name: '赛末点', condition: '快速游戏生存赛经典模式 9 回合结束并获胜', features: [23] },
          { name: '我是岛主', condition: '在「荒岛」取得三星评价', features: [6] },
          { name: '保持呼吸', condition: '通过了「荒岛」关卡', features: [6] },
          { name: '金爪奖', condition: '在「猛兽足球」赢得 5 局快速游戏经典模式', features: [7] },
          { name: '积少成多', condition: '在「棒棒糖工厂」只提交小糖并获胜（快速游戏）', features: [8] },
          { name: '保龄球馆里的猫', condition: '在「猛兽冰球」击打冰球撞飞 2 人以上并进球（快速游戏）', features: [0] },
          { name: '不可能的任务', condition: '在「黑洞实验室」第二次浮空前获得胜利（快速游戏）', features: [3] },
          { name: '头号玩家', condition: '在「进入游戏」赢得 5 局快速游戏经典模式', features: [9] },
          { name: '爷回来了', condition: '在「棒棒糖工厂」从提交点爬出来（快速游戏）', features: [8] },
          { name: '鳄口脱险', condition: '在「鳄霸谷」赢得 5 局快速游戏经典模式', features: [10] },
          { name: '海獭突击队', condition: '在「猛兽潜艇」赢得 5 局快速游戏经典模式', features: [11] },
          { name: '球类武器', condition: '在「猛兽橄榄球」长传并砸晕对手（快速游戏）', features: [12] },
          { name: '野鸭变凤凰', condition: '在「猛兽冰球」赢得 5 局快速游戏经典模式', features: [0] },
          { name: '全面战争', condition: '在「炸弹投石机」赢得 5 局快速游戏经典模式', features: [13] },
          { name: '火车进站', condition: '在「荒野大膘客」赢得 5 局快速游戏经典模式', features: [1] },
          { name: '极度干燥', condition: '在「猛兽潜艇」不掉入水中并获得回合胜利（快速游戏）', features: [11] },
          { name: '幸存者', condition: '在「暴风雪」赢得 5 局快速游戏经典模式', features: [15] },
          { name: '毛量级冠军', condition: '在「加肥擂台」赢得 5 局快速游戏经典模式', features: [16] },
          { name: '十万伏特', condition: '在「猛兽电击球」赢得 5 局快速游戏经典模式', features: [5] },
          { name: '魂断烂桥', condition: '在「断桥」赢得 5 局快速游戏经典模式', features: [17] },
          { name: 'G-Man', condition: '在「黑洞实验室」赢得 5 局快速游戏经典模式', features: [3] },
          { name: '赢了！地球上最强猛兽', condition: '在「武道会」赢得 5 局快速游戏经典模式', features: [18] },
          { name: '无敌破坏王', condition: '在「风洞」所有拉杆被破坏后存活（快速游戏）', features: [4] },
          { name: '笑到最后', condition: '在领奖台拍照一刻只有自己没有被击晕', features: [23] },
          { name: '坚持再坚持', condition: '连续 3 周完成所有的每周挑战', features: [23] },
          { name: '等级 100 级', condition: '猛兽等级达到 100 级', features: [23] },
          { name: '虎胆龙威', condition: '在「断箭行动」赢得 5 局快速游戏经典模式', features: [19] },
          { name: '和平精英', condition: '在「断桥」不打人并获得回合胜利（快速游戏）', features: [17] },
          { name: '人猿泰山', condition: '在「断桥」的主绳断裂后坚持 20 秒并获得回合胜利（快速游戏）', features: [17] },
          { name: '冰狗', condition: '在「碎裂浮冰」赢得 5 局快速游戏经典模式', features: [14] },
          { name: '梦之队', condition: '和朋友组队并连续赢得 5 局快速游戏胜利', features: [23] },
          { name: '超级碗', condition: '在「猛兽橄榄球」赢得 5 局快速游戏经典模式', features: [12] },
          { name: '风平浪静', condition: '在「鳄霸谷」的第三波浪到来之前获得回合胜利（快速游戏）', features: [10] },
          { name: '真狗快打', condition: '在「进入游戏」一局游戏内击晕正在街机游戏内的对手 3 次（快速游戏）', features: [9] },
          { name: '风中划水', condition: '在「风洞」完全不抓拉杆和闸门并获得回合胜利（快速游戏）', features: [4] },
          { name: '当红炸子鸡', condition: '快速游戏连胜 5 局', features: [23] },
          { name: '盖了帽了', condition: '在「猛兽潜艇」将玩家扔到导弹舱盖内淘汰（快速游戏）', features: [11] },
          { name: '兄弟连', condition: '和朋友组队并赢得 10 局快速游戏胜利', features: [23] },
          { name: '小菜一碟', condition: '快速游戏生存赛经典模式 3 回合结束并获胜', features: [23] },
          { name: '你不要回来了', condition: '在「武道会」把对手打飞到赛场外并淘汰（快速游戏）', features: [18] },
          { name: '阿甘快跑', condition: '在「猛兽橄榄球」回合开始 15 秒内进球（快速游戏）', features: [12] },
          { name: '描边大师', condition: '在「加肥擂台」任意回合内不碰到任何落石或者火焰并获胜（快速游戏）', features: [16] },
          { name: '铁人麦克', condition: '在「加肥擂台」于 91 秒内获得回合胜利（快速游戏）', features: [16] },
          { name: '尼莫船长', condition: '在「黑帆」单人模式取得三星评价', features: [20] },
          { name: '给我个五', condition: '和朋友组队完成 10 局快速游戏', features: [23] },
          { name: '等级 50 级', condition: '猛兽等级达到 50 级', features: [23] },
          { name: '落水狗', condition: '在「鳄霸谷」回合结束时和队友都在水中并取得回合胜利（快速游戏）', features: [10] },
          { name: '速度与柯基', condition: '在猛兽卡丁车「上海」中，于 2:38.00 内完成一局比赛（快速游戏）', features: [21] },
          { name: '有乐同享', condition: '自定义房间添加多位本地玩家并完成 2 局游戏', features: [23] },
          { name: '猫朋狗友', condition: '新增 10 个游戏内好友', features: [23] },
          { name: '新兵营', condition: '和朋友组队并赢得 1 局快速游戏胜利', features: [23] },
          { name: '遵命，船长！', condition: '通过了「黑帆」单人模式', features: [20] },
          { name: '极品飞狗', condition: '在「实验室」取得三星评价', features: [2] },
          { name: '我有个朋友', condition: '和朋友组队完成 1 局快速游戏', features: [23] },
          { name: '我做主', condition: '自定义房间更改自定义设置并完成 1 局游戏', features: [23] },
          { name: '罗伊·马凯', condition: '在「猛兽足球」回合开始 10 秒内进球（快速游戏）', features: [7] },
          { name: '哪儿有风', condition: '在「风洞」不被风吹到过并存活超过 45 秒（快速游戏）', features: [4] },
          { name: '弗地冈人', condition: '在「黑洞实验室」第四次黑洞浮空时不借助锁链并生还（快速游戏）', features: [3] },
          { name: '老铁来了', condition: '新增 1 个游戏内好友', features: [23] },
          { name: '快速游戏 10 胜', condition: '快速游戏获胜 10 局', features: [23] },
          { name: '打卡上班', condition: '一周内完成 4 个每周挑战', features: [23] },
          { name: '头像达人', condition: '解锁 15 款头像', features: [23] },
          { name: '时尚时尚最时尚', condition: '收集超过 30 个角色皮肤', features: [23] },
          { name: '动物解锁：20', condition: '解锁 20 个角色', features: [23] },
          { name: '谁干的', condition: '比赛内观战视角用道具砸中 5 名对手（游戏结束时不少于 6 名真人玩家）', features: [23] },
          { name: '皮肤解锁：20', condition: '收集超过 20 个角色皮肤', features: [23] },
          { name: '体育精神', condition: '在领奖台击晕 1 名玩家', features: [23] },
          { name: '安全第一', condition: '猛兽卡丁车获胜 1 局（快速游戏）', features: [23] },
          { name: '亚瑟的梦', condition: '在「黑洞实验室」浮空过程中击晕 1 名玩家（快速游戏）', features: [3] },
          { name: '稳如老狗', condition: '在「碎裂浮冰」不掉入水中并获得回合胜利（快速游戏）', features: [14] },
          { name: '杰克与萝丝', condition: '在「碎裂浮冰」同队两人都存活到回合获胜（快速游戏）', features: [14] },
          { name: '热狗', condition: '在「暴风雪」不被冻住并获得回合胜利（快速游戏）', features: [15] },
          { name: '冲浪狗', condition: '在「鳄霸谷」和队友不掉下浮桥并获得回合胜利（快速游戏）', features: [10] },
          { name: '牛啊', condition: '不被击晕赢得 1 局快速游戏胜利', features: [23] },
          { name: '小试牛刀', condition: '快速游戏获胜 1 局', features: [23] },
          { name: '欢迎来到派对', condition: '通过了「实验室」关卡', features: [2] },
          { name: '白金动物', condition: '解锁 92 个成就', features: [23] },
          { name: '打遍天下', condition: '自定义房间获得 20 张不同地图的胜利（游戏结束时不少于 6 名真人玩家）', features: [23] },
          { name: '寒冰屏障', condition: '在「武道会」通过冻住自己以避免被毒雾淘汰来获得回合胜利（快速游戏）', features: [18] },
          { name: '天降正义', condition: '在「武道会」从中间任意柱子跳下并击晕一名玩家（快速游戏）', features: [18] },
          { name: '窜天猴', condition: '在「猛兽潜艇」一回合内抓 3 次导弹升空各 1 秒以上（快速游戏）', features: [11] },
          { name: '安全降落', condition: '在「断箭行动」一回合内存活超过 2 分 30 秒（快速游戏）', features: [19] },
          { name: '不像帕特·罗奇那样', condition: '在「断箭行动」抓住螺旋桨旋转一圈并存活（快速游戏）', features: [19] },
          { name: '荒野求生', condition: '在「暴风雪」掉到湖的洞里并爬回火堆旁（快速游戏）', features: [15] },
          { name: '威利·旺卡', condition: '在「棒棒糖工厂」赢得 5 局快速游戏经典模式', features: [8] },
          { name: '打工狗', condition: '在「荒野大膘客」连续投煤 10 块且中途不被淘汰（快速游戏）', features: [1] },
          { name: '生物燃料', condition: '在「荒野大膘客」一局游戏内将敌人投进煤炉 10 次（快速游戏）', features: [1] },
          { name: '钻石商人', condition: '在「进入游戏」一局游戏内单人获得 20 个钻石并获胜（快速游戏）', features: [9] },
          { name: '淘金客', condition: '在「进入游戏」一局游戏内单人获得 50 个金币并获胜（快速游戏）', features: [9] },
          { name: '带我去月球', condition: '在「矿山夺宝」赢得 5 局快速游戏经典模式', features: [22] },
          { name: '飞狗环游记', condition: '在「矿山夺宝」一局游戏内抓住气球在空中飘浮超过 60 秒（快速游戏）', features: [22] },
          { name: '矿车狂热', condition: '在「矿山夺宝」将煤矿车推下悬崖（快速游戏）', features: [22] },
          { name: '赚快钱', condition: '在「矿山夺宝」游戏开始 30 秒内得分（快速游戏）', features: [22] },
          { name: '拆弹部队', condition: '在「炸弹投石机」一局游戏内排除炸药桶爆炸 10 次（快速游戏）', features: [13] },
          { name: '猩空联盟会员', condition: '在「炸弹投石机」一局游戏内乘坐 10 次投石机（快速游戏）', features: [13] },
          { name: '666', condition: '在「猛兽电击球」单人投进一局内所有的己方进球并获胜（快速游戏）', features: [5] },
          { name: '科怀·伦纳德', condition: '在「猛兽电击球」的第 11 回合的最后 10 秒内进球（快速游戏）', features: [5] },
          { name: '帽子戏法', condition: '在「猛兽足球」一局游戏内拿下 3 粒进球（快速游戏）', features: [7] },
          { name: '身体健全', condition: '在困难或猛兽难度下完成「黑帆」双人模式', features: [20] },
          { name: '干杯，宝贝们！', condition: '在猛兽难度下完成「黑帆」双人模式', features: [20] },
          { name: '威尔逊', condition: '在「荒岛」找到并捡起威尔逊排球', features: [6] },
          { name: '秋名山猛兽', condition: '在猛兽卡丁车「上海」中，一局完成飘移加速 34 次（快速游戏）', features: [21] },
      ]
    }
  };

  // --- 页面配置 ---
  const pageConfigs = {
    // 动物页配置
    '动物特征分类': {
      dataKey: 'animals',
      filterType: 'multi-select', // 多选
      itemType: '动物',
      renderItem: (animal) => {
        const li = document.createElement('li');
        li.className = 'card';
        
        const img = document.createElement('img');
        img.src = `images/${animal.name}.png`;
        img.alt = animal.name;
        img.className = 'animal-avatar';
        img.loading = 'lazy';
        
        const name = document.createElement('span');
        name.textContent = animal.name;
        
        li.append(img, name);
        return li;
      }
    },
    // 成就页配置
    '成就地图分类': {
      dataKey: 'achievements',
      filterType: 'single-select', // 单选
      itemType: '成就',
      renderItem: (ach) => {
        const li = document.createElement('li');
        li.className = 'card';

        const img = document.createElement('img');
        img.className = 'animal-avatar';
        img.alt = ach.name;
        img.loading = 'lazy';
        img.src = `images/achievements/${ach.name}.jpg`;
        img.onerror = () => { img.style.display = 'none'; };

        const title = document.createElement('span');
        title.textContent = ach.name;

        const tip = document.createElement('small');
        tip.textContent = ach.condition || '（无完成条件）';

        li.append(img, title, tip);
        return li;
      }
    }
  };

  // --- DOM 元素缓存 ---
  const categoryButtonsContainer = document.getElementById('categoryButtons');
  const resultList = document.getElementById('resultList');
  const summaryText = document.getElementById('summaryText');
  const clearButton = document.getElementById('clearButton');
  const pageTitle = document.querySelector('h1')?.textContent;
  
  // 如果找不到标题或者配置，则不执行
  if (!pageTitle || !pageConfigs[pageTitle]) {
    console.error('Page configuration not found for title:', pageTitle);
    return;
  }

  // --- 全局变量 ---
  const config = pageConfigs[pageTitle];
  const data = dataSources[config.dataKey];
  let selectedFeatures = new Set();

  // --- 函数 ---

  /** 更新清空按钮状态 */
  const updateClearButtonState = () => {
    clearButton.disabled = selectedFeatures.size === 0;
  };

  /** 渲染结果 */
  const displayResults = () => {
    // 1. 过滤
    const matches = data.items.filter(item => {
      // 如果没有选中任何特征，则显示所有
      if (selectedFeatures.size === 0) return true;
      // “与”逻辑：必须包含所有选中的特征
      return [...selectedFeatures].every(featureIndex => item.features.includes(featureIndex));
    });

    // 2. 清空
    resultList.innerHTML = '';

    // 3. 渲染
    if (matches.length > 0) {
      const fragment = document.createDocumentFragment();
      matches.forEach(item => {
        const card = config.renderItem(item); // 使用配置的渲染函数
        fragment.appendChild(card);
      });
      resultList.appendChild(fragment);
    } else {
      const li = document.createElement('li');
      li.textContent = `未找到匹配的${config.itemType}`;
      resultList.appendChild(li);
    }

    // 4. 更新摘要
    if (selectedFeatures.size > 0) {
      const tags = [...selectedFeatures].map(i => data.features[i]).join('、');
      summaryText.textContent = `拥有“${tags}”特征的${config.itemType}，共 ${matches.length} 个`;
    } else {
      summaryText.textContent = `所有${config.itemType}，共 ${data.items.length} 个`;
    }

    // 5. 更新按钮状态
    updateClearButtonState();
  };
  
  /** 处理特征按钮点击 */
  const handleFeatureToggle = (index, buttonElement) => {
    const isSelected = buttonElement.classList.contains('selected');

    if (config.filterType === 'single-select') {
      // --- 单选逻辑 ---
      // 清除所有已选
      document.querySelectorAll('.category-btn.selected').forEach(btn => {
        btn.classList.remove('selected');
        btn.setAttribute('aria-pressed', 'false');
      });
      selectedFeatures.clear();
      // 如果当前按钮不是之前选中的那个，则选中它
      if (!isSelected) {
        buttonElement.classList.add('selected');
        buttonElement.setAttribute('aria-pressed', 'true');
        selectedFeatures.add(index);
      }
    } else {
      // --- 多选逻辑 (默认) ---
      buttonElement.classList.toggle('selected');
      const nowSelected = buttonElement.classList.contains('selected');
      buttonElement.setAttribute('aria-pressed', nowSelected);
      if (nowSelected) {
        selectedFeatures.add(index);
      } else {
        selectedFeatures.delete(index);
      }
    }

    displayResults();
  };

  /** 清空所有选择 */
  const clearAll = () => {
    selectedFeatures.clear();
    document.querySelectorAll('.category-btn.selected').forEach(btn => {
      btn.classList.remove('selected');
      btn.setAttribute('aria-pressed', 'false');
    });
    displayResults();
  };

  /** 初始化应用 */
  const init = () => {
    // 动态生成按钮
    const buttonsFragment = document.createDocumentFragment();
    data.features.forEach((feature, index) => {
      const button = document.createElement('button');
      button.className = 'category-btn';
      button.textContent = feature;
      button.dataset.featureIndex = index;
      button.setAttribute('aria-pressed', 'false');
      buttonsFragment.appendChild(button);
    });
    categoryButtonsContainer.appendChild(buttonsFragment);

    // 使用事件委托绑定点击事件
    categoryButtonsContainer.addEventListener('click', (event) => {
      const clickedButton = event.target.closest('.category-btn');
      if (clickedButton) {
        const featureIndex = parseInt(clickedButton.dataset.featureIndex, 10);
        handleFeatureToggle(featureIndex, clickedButton);
      }
    });

    clearButton.addEventListener('click', clearAll);

    // 初始渲染
    displayResults();
  };

  // --- 启动 ---
  init();
});