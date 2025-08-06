# src/domain/entities/purchase_settings.py
from dataclasses import dataclass, field
from typing import List, Dict, Any
import re
from datetime import datetime


@dataclass
class PurchaseSettings:
    """로또 구매 설정 엔티티"""
    
    schedule_time: str  # HH:MM 형식
    purchase_count: int
    lotto_list: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """생성 후 검증"""
        self._validate()
    
    def _validate(self):
        """구매 설정 검증"""
        # 시간 형식 검증 (HH:MM)
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, self.schedule_time):
            raise ValueError(f"잘못된 시간 형식입니다: {self.schedule_time}. HH:MM 형식이어야 합니다.")
        
        # 구매 수량 검증
        if not isinstance(self.purchase_count, int) or self.purchase_count < 1 or self.purchase_count > 5:
            raise ValueError("구매 수량은 1~5개 사이여야 합니다.")
        
        # 로또 리스트 검증
        if len(self.lotto_list) > self.purchase_count:
            raise ValueError("로또 리스트가 구매 수량보다 많습니다.")
        
        # 각 로또 설정 검증
        for i, lotto in enumerate(self.lotto_list):
            self._validate_lotto_item(lotto, i)
    
    def _validate_lotto_item(self, lotto: Dict[str, Any], index: int):
        """개별 로또 설정 검증"""
        if "type" not in lotto:
            raise ValueError(f"로또 [{index}]: 'type' 필드가 필요합니다.")
        
        lotto_type = lotto["type"]
        numbers = lotto.get("numbers", [])
        
        valid_types = ["자동", "수동", "반자동", "AI추천", "통계분석"]
        if lotto_type not in valid_types:
            raise ValueError(f"로또 [{index}]: 유효하지 않은 타입입니다. {valid_types} 중 하나여야 합니다.")
        
        # 번호 검증
        if lotto_type == "수동" and len(numbers) != 6:
            raise ValueError(f"로또 [{index}]: 수동 선택은 6개의 번호가 필요합니다.")
        
        if lotto_type == "반자동" and len(numbers) != 3:
            raise ValueError(f"로또 [{index}]: 반자동 선택은 3개의 번호가 필요합니다.")
        
        # 번호 범위 검증 (1~45)
        for num in numbers:
            if not isinstance(num, int) or num < 1 or num > 45:
                raise ValueError(f"로또 [{index}]: 번호는 1~45 사이의 정수여야 합니다.")
        
        # 중복 번호 검증
        if len(numbers) != len(set(numbers)):
            raise ValueError(f"로또 [{index}]: 중복된 번호가 있습니다.")
    
    def is_valid(self) -> bool:
        """설정이 유효한지 확인"""
        try:
            self._validate()
            return True
        except ValueError:
            return False
    
    def get_schedule_datetime(self, target_date: datetime = None) -> datetime:
        """스케줄 시간을 datetime 객체로 반환"""
        if target_date is None:
            target_date = datetime.now()
        
        hour, minute = map(int, self.schedule_time.split(':'))
        return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    def add_lotto_setting(self, lotto_type: str, numbers: List[int] = None):
        """로또 설정 추가"""
        if numbers is None:
            numbers = []
        
        if len(self.lotto_list) >= self.purchase_count:
            raise ValueError("더 이상 로또 설정을 추가할 수 없습니다.")
        
        lotto_setting = {"type": lotto_type, "numbers": numbers}
        self._validate_lotto_item(lotto_setting, len(self.lotto_list))
        self.lotto_list.append(lotto_setting)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "schedule_time": self.schedule_time,
            "count": self.purchase_count,
            "lotto_list": self.lotto_list.copy()
        }
