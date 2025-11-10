import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SelectedCollectionComponent } from './selected-collection.component';

describe('SelectedTopicComponent', () => {
  let component: SelectedCollectionComponent;
  let fixture: ComponentFixture<SelectedCollectionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SelectedCollectionComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SelectedCollectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
