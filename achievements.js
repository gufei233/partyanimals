// features, achievements, selectedFeatures, toggleFeature, clearAll, displayResults, renderButtons

// --------------- 地图特征（按钮顺序固定；“其他”在最后） ---------------
const features = [
  '猛兽冰球','荒野大膘客','实验室','黑洞实验室','风洞',
  '猛兽电击球','荒岛','猛兽足球','棒棒糖工厂','进入游戏',
  '鳄霸谷','猛兽潜艇','猛兽橄榄球','炸弹投石机','碎裂浮冰',
  '暴风雪','加肥擂台','断桥','武道会','断箭行动',
  '黑帆','上海','矿山夺宝','其他'
];

const achievements = [
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
];

// =============== 以下为与动物版一致的全局逻辑（按钮动态生成 + 多选 AND 过滤） ===============
var selectedFeatures = new Set();

function updateClearButtonState() {
  var btn = document.getElementById('clearButton');
  if (btn) btn.disabled = selectedFeatures.size === 0;
}

function displayResults() {
  var resultList = document.getElementById('resultList');
  var summaryText = document.getElementById('summaryText');
  var matches = achievements.filter(function(a){
    return Array.from(selectedFeatures).every(function(i){ return a.features.includes(i); });
  });

  resultList.innerHTML = '';
  if (matches.length) {
    var frag = document.createDocumentFragment();
    matches.forEach(function(a){
      var li = document.createElement('li');
      li.className = 'card';

      var img = document.createElement('img');
      img.className = 'animal-avatar';
      img.alt = a.name;
      img.loading = 'lazy';
      img.src = 'images/achievements/' + a.name + '.jpg';
      // 只用本地图；缺图时隐藏，不做远程兜底
      img.onerror = function(){ img.style.display = 'none'; };

      var title = document.createElement('span');
      title.textContent = a.name;

      var tip = document.createElement('small');
      tip.style.marginTop = '6px';
      tip.style.opacity = '0.8';
      tip.textContent = a.condition || '（无完成条件）';

      li.append(img, title, tip);
      frag.appendChild(li);
    });
    resultList.appendChild(frag);
  } else {
    var li = document.createElement('li');
    li.textContent = '未找到匹配的成就';
    resultList.appendChild(li);
  }

  if (selectedFeatures.size) {
    var tags = Array.from(selectedFeatures).map(function(i){ return features[i] + '的成就'; }).join('、');
    summaryText.textContent = tags + '，共 ' + matches.length + ' 个';
  } else {
    summaryText.textContent = '所有成就，共 ' + achievements.length + ' 个';
  }
  updateClearButtonState();
}

function toggleFeature(index, btn) {
  // 当前这个是否已经选中
  var already = btn.classList.contains('selected');

  // 1) 取消所有已选
  document.querySelectorAll('.category-btn.selected').forEach(function(b){
    b.classList.remove('selected');
    b.setAttribute('aria-pressed','false');
  });
  selectedFeatures.clear();

  // 2) 如果之前没选中这个按钮 -> 仅选中它；否则保持“全不选”
  if (!already) {
    btn.classList.add('selected');
    btn.setAttribute('aria-pressed','true');
    selectedFeatures.add(index);
  }

  displayResults();
}


function clearAll() {
  selectedFeatures.clear();
  document.querySelectorAll('.category-btn.selected').forEach(function(btn){
    btn.classList.remove('selected');
    btn.setAttribute('aria-pressed','false');
  });
  displayResults();
}

function renderButtons() {
  var container = document.getElementById('categoryButtons');
  if (!container) return;
  var frag = document.createDocumentFragment();
  features.forEach(function(f, i){
    var btn = document.createElement('button');
    btn.className = 'category-btn';
    btn.textContent = f;
    btn.setAttribute('aria-pressed','false');
    btn.onclick = function(){ toggleFeature(i, btn); };
    frag.appendChild(btn);
  });
  container.appendChild(frag);
}

// 初始化（与动物版一致）
document.addEventListener('DOMContentLoaded', function(){
  renderButtons();
  var clearButton = document.getElementById('clearButton');
  if (clearButton && !clearButton._bound) {
    clearButton._bound = true;
    clearButton.addEventListener('click', clearAll);
  }
  displayResults();
});
