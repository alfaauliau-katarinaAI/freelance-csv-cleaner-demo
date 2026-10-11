(function(root){
  'use strict';
  function nonNegative(x) { const n = Number(x); return Number.isFinite(n) && n >= 0 ? n : 0; }
  function calculate(model) {
    model = model || {};
    const warnings=[];
    function field(v, label, max){
      if(v==='' || v===null || v===undefined || !Number.isFinite(Number(v)) || Number(v)<0 || (max!==undefined && Number(v)>max)) {
        warnings.push(label+' harus berupa angka valid antara 0 dan '+(max===undefined?'tak terbatas':max)+'.');
      }
      return nonNegative(v);
    }
    const nPortions=field(model.portions,'Jumlah porsi');
    if(!Number.isInteger(nPortions) || nPortions<1) warnings.push('Jumlah porsi harus bilangan bulat minimal 1.');
    const portions = Math.max(1, Math.floor(nPortions || 1));
    const ingredients = (Array.isArray(model.ingredients) ? model.ingredients : []).map(function(item,index){
      const label='Bahan '+(index+1);
      const packQty = field(item.packQty,label+' isi kemasan');
      const price = field(item.packPrice,label+' harga beli');
      const usage = field(item.usage,label+' pemakaian');
      const wasteValue=field(item.waste,label+' waste',100);
      if(packQty<=0)warnings.push(label+' isi kemasan harus lebih dari 0; HPP belum aman untuk digunakan.');
      if(wasteValue>100)warnings.push(label+' waste maksimal 100%.');
      const unitPrice = packQty>0 ? price/packQty : 0;
      const waste = Math.min(100,wasteValue);
      const cost = unitPrice*usage*(1+waste/100);
      return {name: String(item.name || 'Bahan'), cost, unitPrice};
    });
    if(!ingredients.length)warnings.push('Masukkan setidaknya satu bahan.');
    const ingredientCost = ingredients.reduce((s,x)=>s+x.cost,0);
    const packaging = field(model.packaging,'Kemasan')*portions;
    const overhead = field(model.overhead,'Overhead');
    const total = ingredientCost + packaging + overhead;
    const hpp = total/portions;
    const marginValue=field(model.margin,'Target margin',99);
    if(marginValue>99)warnings.push('Margin harus di bawah 100%.');
    const margin = Math.min(99,marginValue);
    const rawPrice = hpp/(1-margin/100);
    const recommendedPrice=Math.ceil(rawPrice/500)*500;
    const profit=recommendedPrice-hpp;
    if(!Number.isFinite(recommendedPrice))warnings.push('Hasil perhitungan tidak valid; periksa angka yang dimasukkan.');
    return {portions,ingredients,ingredientCost,packaging,overhead,total,hpp,margin,rawPrice,
      recommendedPrice: Number.isFinite(recommendedPrice)?recommendedPrice:0,
      profit:Number.isFinite(profit)?profit:0,
      realizedMargin:recommendedPrice>0?profit/recommendedPrice*100:0,
      valid:warnings.length===0,warnings};
  }
  root.HppCalc={calculate};
  if(typeof module!=='undefined' && module.exports)module.exports={calculate};
})(typeof window!=='undefined'?window:globalThis);
