/* ===== 天気服装 - Recommendation Engine ===== */

const Recommend = {
  // Temperature zone definitions
  TEMP_ZONES: [
    { name: '極寒',   min: -Infinity, max: 5,  needsOuter: 5, needsBase: 4, needsMiddle: true },
    { name: '寒い',   min: 5,  max: 10, needsOuter: 4, needsBase: 3, needsMiddle: true },
    { name: 'やや寒い', min: 10, max: 15, needsOuter: 3, needsBase: 2, needsMiddle: false },
    { name: '快適',   min: 15, max: 22, needsOuter: 2, needsBase: 2, needsMiddle: false },
    { name: 'やや暑い', min: 22, max: 28, needsOuter: 0, needsBase: 1, needsMiddle: false },
    { name: '暑い',   min: 28, max: Infinity, needsOuter: 0, needsBase: 1, needsMiddle: false }
  ],

  generate(weatherData) {
    const wardrobe = Wardrobe.getAll();
    if (wardrobe.length === 0) return null;

    const settings = Storage.getSettings();
    const mode = Weather.getTimeMode();
    const summary = Weather.getSummaryForMode(weatherData, mode);
    const periods = Weather.getPeriodsForMode(weatherData, mode);
    const sensitivity = this._getSensitivityOffset(settings.sensitivity);

    // Adjust temps for sensitivity
    const effectiveMin = summary.minTemp + sensitivity;
    const effectiveMax = summary.maxTemp + sensitivity;
    const effectiveTempDiff = effectiveMax - effectiveMin;

    // Determine zones
    const minZone = this._getZone(effectiveMin);
    const maxZone = this._getZone(effectiveMax);

    // Build outfit
    const outfit = {};
    const timeline = [];
    const carryItems = [];

    // Base layer - chosen for the warmest part of remaining day
    outfit.base = this._pickItem(wardrobe, 'tops', maxZone.needsBase, summary, weatherData);

    // Bottoms
    outfit.bottoms = this._pickItem(wardrobe, 'bottoms', minZone.needsBase, summary, weatherData);

    // Outer layer - based on coldest part of remaining day
    if (minZone.needsOuter >= 2) {
      outfit.outer = this._pickItem(wardrobe, 'outerwear', minZone.needsOuter, summary, weatherData);
    }

    // Shoes
    outfit.shoes = this._pickShoes(wardrobe, summary, weatherData);

    // Accessories based on weather
    outfit.accessories = this._pickAccessories(wardrobe, summary, weatherData);

    // Build timeline based on mode
    this._buildTimeline(timeline, periods, outfit, effectiveTempDiff, mode);

    // Carry items
    this._buildCarryItems(carryItems, outfit, summary, periods, effectiveMax, effectiveTempDiff, mode);

    return {
      date: weatherData.date,
      mode,
      weather: summary,
      items: outfit,
      timeline,
      carryItems,
      zoneName: minZone.name + '〜' + maxZone.name,
      message: this._generateMessage(summary, effectiveMin, effectiveMax, mode)
    };
  },

  _buildTimeline(timeline, periods, outfit, tempDiff, mode) {
    const PERIOD_LABELS = { '朝': 'morning', '昼': 'afternoon', '夕': 'evening', '夜': 'night' };

    if (mode.key === 'morning') {
      // Full day
      if (tempDiff >= 10) {
        timeline.push({ period: '朝', temp: periods[0].temp, action: `${outfit.outer ? outfit.outer.name + 'を羽織って出発' : '暖かくして出発'}` });
        timeline.push({ period: '昼', temp: periods[1].temp, action: `${outfit.outer ? outfit.outer.name + 'を脱いでOK' : outfit.base ? outfit.base.name + 'で快適' : '快適に過ごせる'}` });
        timeline.push({ period: '夕', temp: periods[2].temp, action: '気温が下がり始める' });
        timeline.push({ period: '夜', temp: periods[3].temp, action: `${outfit.outer ? '再び' + outfit.outer.name + 'を羽織る' : '上着があると安心'}` });
      } else if (tempDiff >= 5) {
        timeline.push({ period: '朝', temp: periods[0].temp, action: `${outfit.outer ? outfit.outer.name + 'を羽織って出発' : 'そのまま出発'}` });
        timeline.push({ period: '昼', temp: periods[1].temp, action: `${outfit.outer ? '脱いでも脱がなくてもOK' : '快適に過ごせる'}` });
        timeline.push({ period: '夜', temp: periods[3].temp, action: '一日同じ服装で大丈夫' });
      } else {
        timeline.push({ period: '終日', temp: Math.round((periods[0].temp + periods[1].temp) / 2), action: '気温差が少ないので一日同じ服装で快適' });
      }
    } else if (mode.key === 'afternoon') {
      // Afternoon onward
      if (tempDiff >= 5) {
        timeline.push({ period: '昼', temp: periods[0].temp, action: `今の気温で${outfit.base ? outfit.base.name : '快適'}` });
        timeline.push({ period: '夕〜夜', temp: periods[periods.length - 1].temp, action: `${outfit.outer ? 'この後' + outfit.outer.name + 'が必要になる' : '気温が下がるので注意'}` });
      } else {
        timeline.push({ period: '午後〜夜', temp: periods[0].temp, action: 'この後も気温変化は少なめ。このままで大丈夫' });
      }
    } else {
      // Evening
      if (periods.length >= 2 && Math.abs(periods[0].temp - periods[1].temp) >= 3) {
        timeline.push({ period: '夕方', temp: periods[0].temp, action: `${outfit.outer ? outfit.outer.name + 'を持って出発' : 'そのまま出発'}` });
        timeline.push({ period: '夜', temp: periods[1].temp, action: `さらに冷え込む。${outfit.outer ? outfit.outer.name + 'を着る' : '暖かくして'}` });
      } else {
        timeline.push({ period: '夕〜夜', temp: periods[0].temp, action: 'これからの時間はこの服装で大丈夫' });
      }
    }
  },

  _buildCarryItems(carryItems, outfit, summary, periods, effectiveMax, effectiveTempDiff, mode) {
    // Outer removal for warm midday
    if (mode.key === 'morning' && outfit.outer && effectiveTempDiff >= 8) {
      carryItems.push({ name: '脱いだ' + outfit.outer.name, reason: '昼は暑くなる' });
    }

    // Rain check for remaining periods
    const hasRainAhead = periods.some(p => p.rainProbability >= 50);
    const hasLightRainAhead = periods.some(p => p.rainProbability >= 30);

    if (hasRainAhead) {
      const hasUmbrella = outfit.accessories?.some(a => a.subCategory === 'umbrella');
      if (!hasUmbrella) carryItems.push({ name: '折り畳み傘', reason: 'この後雨予報あり' });
    } else if (hasLightRainAhead) {
      carryItems.push({ name: '折り畳み傘', reason: '念のため（降水確率30%以上）' });
    }

    if (effectiveMax >= 25 && summary.dominantWeather === 'sunny') {
      const hasSunglasses = outfit.accessories?.some(a => a.subCategory === 'sunglasses');
      if (!hasSunglasses) carryItems.push({ name: 'サングラス', reason: '日差しが強い' });
    }
  },

  _getSensitivityOffset(sensitivity) {
    switch (sensitivity) {
      case 'hot': return 2;
      case 'cold': return -2;
      default: return 0;
    }
  },

  _getZone(temp) {
    return this.TEMP_ZONES.find(z => temp >= z.min && temp < z.max) || this.TEMP_ZONES[3];
  },

  _pickItem(wardrobe, category, targetWarmth, summary, weatherData) {
    const candidates = wardrobe.filter(item => {
      if (item.category !== category) return false;
      if (summary.hasRain && !item.weatherSuitability.includes('rainy') && category === 'outerwear') return false;
      if (summary.dominantWeather === 'snowy' && !item.weatherSuitability.includes('snowy') && category === 'outerwear') return false;
      return true;
    });

    if (candidates.length === 0) return null;

    candidates.sort((a, b) => {
      const diffA = Math.abs(a.warmthLevel - targetWarmth);
      const diffB = Math.abs(b.warmthLevel - targetWarmth);
      if (diffA !== diffB) return diffA - diffB;
      if (a.lastWornAt && !b.lastWornAt) return 1;
      if (!a.lastWornAt && b.lastWornAt) return -1;
      return 0;
    });

    const topN = Math.min(3, candidates.length);
    return candidates[Math.floor(Math.random() * topN)];
  },

  _pickShoes(wardrobe, summary, weatherData) {
    const shoes = wardrobe.filter(item => item.category === 'shoes');
    if (shoes.length === 0) return null;

    if (summary.hasRain || summary.dominantWeather === 'snowy') {
      const rainShoes = shoes.filter(s =>
        s.weatherSuitability.includes('rainy') || s.weatherSuitability.includes('snowy')
      );
      if (rainShoes.length > 0) return rainShoes[Math.floor(Math.random() * rainShoes.length)];
    }

    const suitable = shoes.filter(s => s.weatherSuitability.includes(summary.dominantWeather));
    if (suitable.length > 0) return suitable[Math.floor(Math.random() * suitable.length)];
    return shoes[Math.floor(Math.random() * shoes.length)];
  },

  _pickAccessories(wardrobe, summary, weatherData) {
    const accessories = [];
    const items = wardrobe.filter(i => i.category === 'accessories');

    if (summary.hasRain || summary.hasLightRain) {
      const umbrella = items.find(i => i.subCategory === 'umbrella');
      if (umbrella) accessories.push(umbrella);
    }

    if (summary.minTemp < 8) {
      const scarf = items.find(i => i.subCategory === 'scarf');
      if (scarf) accessories.push(scarf);
      if (summary.minTemp < 5) {
        const gloves = items.find(i => i.subCategory === 'gloves');
        if (gloves) accessories.push(gloves);
      }
    }

    if (summary.maxTemp >= 25 && summary.dominantWeather === 'sunny') {
      const sunglasses = items.find(i => i.subCategory === 'sunglasses');
      if (sunglasses) accessories.push(sunglasses);
      const cap = items.find(i => i.subCategory === 'cap' || i.subCategory === 'hat');
      if (cap) accessories.push(cap);
    }

    return accessories;
  },

  _generateMessage(summary, minTemp, maxTemp, mode) {
    const messages = [];

    // Mode-specific opening
    if (mode.key === 'afternoon') {
      messages.push('午後からのおでかけ向けの提案です');
    } else if (mode.key === 'evening') {
      messages.push('夕方からのおでかけ向けの提案です');
    }

    if (summary.tempDiff >= 10) {
      messages.push(`気温差が${summary.tempDiff}\u00B0Cあります。脱ぎ着できる服装がおすすめ`);
    }

    if (summary.hasRain) {
      messages.push('雨予報があります。撥水性のあるアウターや傘をお忘れなく');
    }

    if (summary.maxWind >= 8) {
      messages.push('風が強い予報です。軽い上着は飛ばされやすいので注意');
    }

    if (maxTemp >= 30) {
      messages.push('猛暑日です。こまめな水分補給を');
    }

    if (minTemp <= 0) {
      messages.push('氷点下になります。しっかり防寒してください');
    }

    if (messages.length === 0) {
      messages.push('過ごしやすい時間帯です');
    }

    return messages.join('。');
  },

  generateAlternative(weatherData, currentOutfit) {
    let attempt = 0;
    let alt;
    do {
      alt = this.generate(weatherData);
      attempt++;
    } while (
      alt && currentOutfit &&
      alt.items.base?.id === currentOutfit.items.base?.id &&
      alt.items.bottoms?.id === currentOutfit.items.bottoms?.id &&
      attempt < 5
    );
    return alt;
  }
};
